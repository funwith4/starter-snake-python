import os
import random

import cherrypy

"""
This is a simple Battlesnake server written in Python.
For instructions see https://github.com/BattlesnakeOfficial/starter-snake-python/README.md
"""


class Battlesnake(object):
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        # This function is called when you register your Battlesnake on play.battlesnake.com
        # It controls your Battlesnake appearance and author permissions.
        # TIP: If you open your Battlesnake URL in browser you should see this data
        return {
            "apiversion": "1",
            "author": "",  # TODO: Your Battlesnake Username
            "color": "#888888",  # TODO: Personalize
            "head": "default",  # TODO: Personalize
            "tail": "default",  # TODO: Personalize
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
        
        def hyp_move(m):
            pass

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
          return c in map(tuple_from_d, body)

        def annotated_is_legal(m):
          new_coords = apply_move(coords, m)
          if not is_in_bounds(new_coords):
            return "out of bounds"
          if is_in_body(new_coords, data["you"]["body"]):
            return "collides with our own body"
          for other_snake in data["board"].get("snakes", []):
            if is_in_body(new_coords, other_snake["body"]):
              return "collides with another snake's body"
            if new_coords == tuple_from_d(other_snake["head"]) and \
              data["you"]["length"] <= other_snake["length"]:
              return "h2h and we'd lose"
          return None

        def is_legal(m):
          annotation = annotated_is_legal(m)
          is_legal = annotation is None
          explanation = "legal" if is_legal else ("illegal [%s]" %annotation)
          new_coords = apply_move(coords, m)
          print(f"Move from {coords} {m.cmd()} to {new_coords} is {explanation}")
          return is_legal
          
        # Choose a random direction to move in
        all_moves = [Move("up", (0,1)),
                     Move("down", (0, -1)),
                     Move("left", (-1, 0)),
                     Move("right", (1, 0))]
        legal_moves = list(filter(is_legal, all_moves))

        cmd = random.choice(legal_moves).cmd()

        print(f">> On turn {data['turn']}, moving {cmd}")
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