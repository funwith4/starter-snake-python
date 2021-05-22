import os
import random

import cherrypy

"""
This is a simple Battlesnake server written in Python.
For instructions see https://github.com/BattlesnakeOfficial/starter-snake-python/README.md
"""
DEATH = -1
ILLEGAL = -2
STUCK = 0.1

class Move(object):
  def __init__(self, cmd, adjuster):
    self._cmd = cmd
    self._adjuster = adjuster

  def __str__(self):
    print("Move(%s)", self._cmd)
  
  def cmd(self):
    return self._cmd

  def adjuster(self):
    return self._adjuster

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
    return f"Move {self.cmd()} is {self.explanation()}"

ALL_MOVES = [Move("up", (0,1)),
             Move("down", (0, -1)),
             Move("left", (-1, 0)),
             Move("right", (1, 0))]

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
            "color": "#736CCB",
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

        def tuple_from_d(coord_dict):
          return (coord_dict["x"], coord_dict["y"])

        def apply_move(coord, m):
          (x, y) = coord
          (dx, dy) = m.adjuster()
          return ((x+dx), (y+dy))

        (h, w) = (data["board"]["height"], data["board"]["width"])
        coords = tuple_from_d(data["you"]["head"])
        
        def is_in_bounds(c):
          (x, y) = c
          if x < 0 or x >= w: return False
          if y < 0 or y >= h: return False
          return True

        def is_in_body(c, body):
          # TODO: This could probably assume that the last segment would be gone.
          return c in map(tuple_from_d, body)

        def i_can_eat(other_snake):
          return data["you"]["length"] > other_snake["length"]

        def potential_head_positions_after_applying_moves(other_snake):
          return list(map(lambda m: apply_move(tuple_from_d(other_snake["head"]), m), ALL_MOVES))

        def evaluate_move(coords, m, depth=0):
          new_coords = apply_move(coords, m)
          
          if not is_in_bounds(new_coords):
            return EvaluatedMove(m, ILLEGAL, "out of bounds")
          if is_in_body(new_coords, data["you"]["body"]):
            return EvaluatedMove(m, DEATH, "collides with our own body")
          
          for other_snake in data["board"].get("snakes", []):
            # NB: We ourselves are an 'other_snake'.
            if other_snake["id"] == data["you"]["id"]: continue
            if is_in_body(new_coords, other_snake["body"]):
              return EvaluatedMove(m, DEATH, "collides with another snake's body")
            if new_coords == tuple_from_d(other_snake["head"]) \
              and not i_can_eat(other_snake):
              return EvaluatedMove(m, DEATH, "h2h and we'd lose")

            # print(f"Eval: {new_coords} in {head_positions_after_applying_moves(other_snake)}, {new_coords in head_positions_after_applying_moves(other_snake)}")
            if new_coords in potential_head_positions_after_applying_moves(other_snake):
              if i_can_eat(other_snake):
                # This doesn't take food into account.
                return EvaluatedMove(m, 2, "potential h2h and we'd win")
              else:
                return EvaluatedMove(m, 0.2, "potential h2h and we'd lose")

          # Use flood-fill to compute space around new_coords.
          # Don't go there if space < length.
          grid = {}
          for snake in data["board"].get("snakes", []):
            grid[tuple_from_d(other_snake["head"])] = 1
            for b in other_snake["body"]:
              grid[tuple_from_d(b)] = 1
          
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
                for nc in map(lambda m: apply_move(n, m),  ALL_MOVES):
                  if is_in_bounds(nc):
                    q.append(nc)  
            return cnt

          length = data["you"]["length"]
          area = capped_flood_count(new_coords, length)
          #print(f"-- We are length {length}, but the area around {new_coords} is at least {area}")
          
          if length > area:
            # boost the score by the area, so if we're running out of space
            # we choose the biggest space.
            return EvaluatedMove(m, STUCK + 0.001 * area, "not going in there, looks like we'll get stuck")
          #Recursive evaluation, but not as good as flood_fill.
          #if depth < 3 and all(map(lambda m: evaluate_move(new_coords, m, depth+1).score() <= STUCK, ALL_MOVES)):
          #  return EvaluatedMove(m, STUCK, "looks like we're stuck")
            #  print(f"-- From {new_coords}, {m1}")

          return EvaluatedMove(m, 1, "legal")

        def instrumented_evaluate_move(coords, m):
          evaluated_move = evaluate_move(coords, m)
          new_coords = apply_move(coords, evaluated_move)
          print(f"Move from {coords} {m.cmd()} to {new_coords} is {evaluated_move.explanation()}")
          return evaluated_move

        # TODO: This should create a list of evaluated_moves, then select randomly from the ones
        # that have good results.

        # Choose a random direction to move in
        evaluated_moves = list(sorted(map(lambda m: instrumented_evaluate_move(coords, m), ALL_MOVES), key=lambda m: m.score(), reverse=True))
        smart_moves = list(filter(lambda m: m.score() >= evaluated_moves[0].score(), evaluated_moves))
        cmd = random.choice(smart_moves).cmd()

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