import os
import random

import cherrypy

"""
This is a simple Battlesnake server written in Python.
For instructions see https://github.com/BattlesnakeOfficial/starter-snake-python/README.md
"""

# Debug mode is more willing to raise errors.
DEBUG = 1


DEATH_AND_CHALLENGE_FAIL = -3
DEATH = -1
ILLEGAL = -2
STUCK = 0.1

LOW_HEALTH_THRESHOLD = 20;
   
class Move(object):
  def __init__(self, cmd, adjuster):
    self._cmd = cmd
    self._adjuster = adjuster

  def __str__(self):
    return f"Move(%{self._cmd}"
  
  def cmd(self):
    return self._cmd

  def adjuster(self):
    return self._adjuster
  
  def __eq__(self, other):
    if not isinstance(other, self.__class__): return False
    return self._cmd == other._cmd and self._adjuster == other._adjuster  

  def ApplyTo(self, coord):
    (dx, dy) = self._adjuster
    return Coord(coord.x() + dx, coord.y() + dy)

ALL_MOVES = [Move("up", (0,1)),
             Move("down", (0, -1)),
             Move("left", (-1, 0)),
             Move("right", (1, 0))]

class EvaluatedMove(Move):
  def __init__(self, m, score, annotation):
    super().__init__(m.cmd(), m.adjuster())
    self._score = score
    self._annotation = annotation

  def score(self):
    return self._score

  def explanation(self):
    if self.score() == -2:
      desc = "ILLEGAL"
    elif self.score() == -1:
      desc = "DEATH"
    else:
      desc = f"LEGAL(score:{self.score()})"
    return f"{desc}: {self._annotation}"

  def __str__(self):
    return f"EvalutedMove {self.cmd()} is {self.explanation()}"

class Coord(object):
  def __init__(self, x, y):
    self._coords = (x, y)

  def FromDict(d):
    return Coord(d['x'], d['y'])

  def __str__(self):
    return f"{self._coords}"
  
  def x(self):
    return self._coords[0]

  def y(self):
    return self._coords[1]

  def __eq__(self, other):
    if not isinstance(other, self.__class__): return False
    return self._coords == other._coords

  def __hash__(self):
    return hash(self._coords)

class Board(object):
  def __init__(self, w, h):
    self._w = w
    self._h = h

  def FromDict(d):
    return Board(w=d["width"], h=d["height"])

  def width(self):
    return self._w

  def height(self):
    return self._h

  def IsInBounds(self, c):
    if c.x() < 0 or c.x() >= self._w: return False
    if c.y() < 0 or c.y() >= self._h: return False
    return True

class Snake(object):
  def __init__(self):
    pass

  def FromDict(d):
    s = Snake()
    s._length = d["length"]
    s._body = list(map(Coord.FromDict, d["body"]))
    return s

  def __str__(self):
    return f"Snake@{self.head()}"
  
  def length(self):
    return self._length

  def head(self):
    return self._body[0]
  
  def body(self):
    return self._body

  def PreviousMove(self):
    "Returns a Move or None if none could be determined."
    if len(self._body) < 2: return None
    previous_head = self._body[1]
    for m in ALL_MOVES:
      if self.head() == m.ApplyTo(previous_head):
        return m
    if DEBUG:
      raise RuntimeError(f"Unable to determine previous move from body: {self.body}")
    return None
  
  def PossibleNextHeadCoords(self):
    return list(map(lambda m: m.ApplyTo(self.head()), ALL_MOVES))

  def Collides(self, c):
    #print(f"{c} is it in {self._body}")
    return c in self._body

  def CanEat(self, other_snake):
    return self._length > other_snake._length


class Battlesnake(object):
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        # This function is called when you register your Battlesnake on play.battlesnake.com
        # It controls your Battlesnake appearance and author permissions.
        # TIP: If you open your Battlesnake URL in browser you should see this data
        print("REGISTER")
        return {
            "apiversion": "1",
            "author": "",  # TODO: Your Battlesnake Username
            "color": "#22c710",
            "head": "tongue",
            "tail": "small-rattle",
        }

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def start(self):
        # This function is called everytime your snake is entered into a game.
        # cherrypy.request.json contains information about the game that's about to be played.
        data = cherrypy.request.json

        print("START")
        return "ok"

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def move(self):
        # This function is called on every turn of a game. It's how your snake decides where to move.
        # Valid moves are "up", "down", "left", or "right".
        # TODO: Use the information in cherrypy.request.json to decide your next move.
        data = cherrypy.request.json

        board = Board.FromDict(data["board"])
        all_snakes = list(map(Snake.FromDict, data["board"]["snakes"]))
        this_snake = Snake.FromDict(data["you"])
        other_snakes = list(map(Snake.FromDict,
            filter(lambda s: s["id"] != data["you"]["id"], data["board"]["snakes"])))

        def delta(coord1, coord2):
          (x1, y1) = coord1
          (x2, y2) = coord2
          return (x1 - x2, y1 - y2)

        def moves(delta):
          (dx, dy) = delta
          return abs(dx) + abs(dy)

        def evaluate_move(snake, m):
          new_coords = m.ApplyTo(this_snake.head())
          
          # TODO:
          #  - We had a bug where we may return an EvaluatedMove, but didn't realize that move put us in to a too-small area, because we didn't fall through to the fill_count.
          #    - Now we've moved the flood_count after DEATH checks, but ahead of the "other_snake" evaluations. 
          #    - TODO: If we _know_ the other_snake is going there and we definitely win, it's good.
          #    - If the other_snake might go somewhere else, we need to discount the score.
          #    
          #  - Avoid food when value is low (high health, no other snakes, short snakes).

          #print(f"Evalution:{this_snake}, from {coords} to {new_coords}")
          if not board.IsInBounds(new_coords):
            return EvaluatedMove(m, ILLEGAL, "out of bounds")
          if this_snake.Collides(new_coords):
            return EvaluatedMove(m, DEATH, "collides with our own body")
          for other_snake in other_snakes:
            if other_snake.Collides(new_coords) and new_coords != other_snake.head():
              return EvaluatedMove(m, DEATH, "collides with another snake's body")

          # Use flood-fill to compute space around new_coords.
          # Don't go there if space < length.
          grid = {}
          for snake in all_snakes:
            for b in snake.body():
              grid[b] = 1

          def capped_flood_count(c, cap):
            cnt = 0
            q = [c]
            while q:
              n = q.pop(0)
              if not n in grid:
                grid[n] = 1
                #print(f"     considering {n} in the area") 
                cnt += 1
                if cnt >= cap: return cnt
                for nc in map(lambda m: m.ApplyTo(n),  ALL_MOVES):
                  if board.IsInBounds(nc):
                    q.append(nc)  
            return cnt

          # We *2 as some arbitrary "we need space" metric.   
          length_with_overhead = this_snake.length() * 2

          area = capped_flood_count(new_coords, length_with_overhead)
          # print(f"-- We are length {length}, but the area around {new_coords} is at least {area}")
          
          if length_with_overhead > area:
            # boost the score by the area, so if we're running out of space
            # we choose the biggest space.
            return EvaluatedMove(m, STUCK + 0.00001 * area, f"prefer not going there, looks like we'll get stuck (area={area})")
          #Recursive evaluation, but not as good as flood_fill.
          #if depth < 3 and all(map(lambda m: evaluate_move(new_coords, m, depth+1).score() <= STUCK, ALL_MOVES)):
          #  return EvaluatedMove(m, STUCK, "looks like we're stuck")
            #  print(f"-- From {new_coords}, {m1}")

          for other_snake in other_snakes:
            # print(f"Eval: {new_coords} in {head_positions_after_applying_moves(other_snake)}, {new_coords in head_positions_after_applying_moves(other_snake)}")

            # print(f"OtherSnake: {other_snake['head']}, ProjectedCoords:{apply_move(tuple_from_d(other_snake['head']), previous_move(other_snake))}")

            if new_coords in other_snake.PossibleNextHeadCoords():
              if this_snake.CanEat(other_snake):
                # TODO: This doesn't take food into account.
                return EvaluatedMove(m, 2, "potential h2h and we'd win")
              else:
                # All things equal, we'll assume it's more likely that the other snake moves in the same direction.
                if new_coords == other_snake.PreviousMove().ApplyTo(other_snake.head()):
                  return EvaluatedMove(m, 0.21, "potential h2h and we'd lose (constant direction)")
                else:
                  return EvaluatedMove(m, 0.22, "potential h2h and we'd lose")
                raise RuntimeError("Inspect me")

          return EvaluatedMove(m, 1, "legal")

        def take_best_class_of_scores(iterable):
          lst = list(iterable)
          lst.sort(key=lambda m: m.score(), reverse=True)
          return filter(lambda m: m.score() >= lst[0].score(), lst)

        def evaluate_food_move(snake, m):
          new_coords = m.ApplyTo(snake.head())
          closest_food_distance = min(moves(delta(new_coords, food_coords)) for food_coords in map(Coord.FromDict, data["board"]["food"]))
          return EvaluatedMove(m, (board.width()*board.height())-closest_food_distance, f"Food boost (d={closest_food_distance}, on move={m})")
        
        # Evaluate the possible moves to find smart ones.
        evaluated_moves = map(lambda m: evaluate_move(this_snake, m), ALL_MOVES)
        smart_moves = take_best_class_of_scores(evaluated_moves)
        if DEBUG:
          evaluated_moves = list(evaluated_moves)
          for em in evaluated_moves:
            new_coords = em.ApplyTo(this_snake.head())
            print(f"  Evaluated Move from {this_snake.head()} {em.cmd()} to {new_coords} is {em.explanation()}")
        
        # If we're low on health, recompute smart moves by moving toward food.
        if data["you"]["health"] < LOW_HEALTH_THRESHOLD:
          evaluated_food_moves = map(lambda m: evaluate_food_move(this_snake.head(), m), smart_moves)
          smart_moves = take_best_class_of_scores(evaluated_food_moves)
        #   if DEBUG:
        #     evaluated_food_moves = list(evaluated_food_moves)
        #     for em in evaluated_food_moves:
        #       new_coords = apply_move(coords, em)
        #       print(f"  Evaluated Food Move from {coords} {em.cmd()} to {new_coords} is {em.explanation()}")

        final_moves = list(smart_moves)
        if DEBUG:
            for em in final_moves:
              new_coords = em.ApplyTo(this_snake.head())
              print(f"  Final Random Choice from {this_snake.head()} {em.cmd()} to {new_coords} is {em.explanation()}")

        cmd = random.choice(final_moves).cmd()

        # Go 10 moves of our own, evaluating the 4 moves each time.
        # Each of those will require 1 movement of each other snake. Choose the best one.
        print(f">> On turn {data['turn']}, moving {cmd} ({data['you']['id']})")
        return {"move": cmd}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def end(self):
        # This function is called when a game your snake was in ends.
        # It's purely for informational purposes, you don't have to make any decisions here.
        data = cherrypy.request.json

        print("END")
        return "ok"


if __name__ == "__main__":
    server = Battlesnake()
    cherrypy.config.update({"server.socket_host": "0.0.0.0"})
    cherrypy.config.update(
        {"server.socket_port": int(os.environ.get("PORT", "8080")),}
    )
    print("Starting Battlesnake Server...")
    cherrypy.quickstart(server)