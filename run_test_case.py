import json
import string
import snake
import sys
from termcolor import colored, cprint

# 
# 'turn'
# 'you.id'
# 'you.health'
# 'you.body'
# 'board.snakes'
# 'board.food'
# 'board.width'
# 'board.height'

def recursive_lower_keys(t):
  if type(t) is dict:
    return dict((k.lower(), recursive_lower_keys(v)) for k,v in t.items())
  elif type(t) is list:
    return list(recursive_lower_keys(e) for e in t)
  else:
    return t

def frame_to_snake(frame_snake):
  d = frame_snake
  d['head'] = frame_snake['body'][0]
  d['length'] = len(frame_snake['body'])
  return d
  
def guess_you_snake_id(frame):
  my_snakes = ["Evie", "Starter Snake Python"]
  name_counts = {}
  you_snake_id = None
  for snake in frame["snakes"]:
    name_counts[snake["name"]] = name_counts.get(snake["name"], 0) + 1
    if snake["name"] in my_snakes: you_snake_id = snake["id"]
  
  my_snake_count = sum(name_counts.get(n, 0) for n in my_snakes)
  if my_snake_count != 1:
    raise RuntimeError(f"Unable to determine 'you' snake:{name_counts}")
  return you_snake_id

def game_and_frame_to_move_request(game, frame, you_snake_id):
  return {
   "turn": frame["turn"],
   "you": next(frame_to_snake(s) for s in frame["snakes"] if s["id"] == you_snake_id),
   "board": {
     "width": game["width"],
     "height": game["height"],
     "snakes": list(frame_to_snake(s) for s in frame["snakes"]),
     "food": frame["food"],
   }
  }

def load_request(game_id, turn_id, you_snake_id=None):
  game_json = recursive_lower_keys(json.load(open(f"testcases/{game_id}.txt", 'r')))
  turn_json = recursive_lower_keys(json.load(open(f"testcases/{game_id}.{turn_id}.txt", 'r')))
  
  frame=turn_json['frames'][0]
  if you_snake_id is None:
    you_snake_id = guess_you_snake_id(frame)
  
  return game_and_frame_to_move_request(game_json['game'], frame, you_snake_id)
  
  
tests = [
  (("1887f9a7-4b82-4ab4-ba09-ac7d13e6d91d", 64),
   [#"down",
    "right"]),  # Gets food boost.
  (("4527eea5-112d-4751-98e3-34ff5043978e", 20),
   ["right"]),  # Empirical
  (("5cc9bc46-9e1d-4cb1-a81c-9f5f50064faa", 84),
   ["down", "up"]),  # Empirical
  (("b5596a02-b0fd-4362-b56f-dcc82ff49fa6", 226),
   ["left", "right"]),  # Empirical
  (("b5596a02-b0fd-4362-b56f-dcc82ff49fa6", 227),
   ["left", "right"]),  # Empirical
  (("c27ec142-7d49-4843-8ccb-a8d991e7f8fe", 35),
   ["left", "right"]),  # Empirical
  (("ba06b5cb-a1ee-49c6-b717-a41a4b9be30b", 173),
   ["left"]),  # Empirical
  (("14cd922a-e15a-4d88-b753-37da9a96e371", 241, "gs_hmgHkJQvtSq6VKfpm4hBRGvd"),
   ["down", "right"]),
  (("14cd922a-e15a-4d88-b753-37da9a96e371", 241, "gs_STRtbf3HMt68PrVhyHcJvbJ6"),
   ["right", "up"]),
  (("52d1a532-e018-41d5-afc0-b52b1eb230dc", 8),
   ["left", "down"]),
  (("14cd922a-e15a-4d88-b753-37da9a96e371", 65, "gs_Y3jwPVMMyVdmq6hQHq9HMtpF"),
   ["left",
    "up"  # Bad move, but that's what we do now- Attempt a trap.
   ]),
   (("6b1acc03-096f-4dbc-b850-646511757613", 81),
   ["up",  # Bad move, but we should realize trap risk.
    "down"]),
   #(("0483c204-7f6a-49ca-8d37-2af81ebc4620", 135),
   #[#"right",  # Bad move, but we should realize trap risk.
   # "left"]),
]

snake.DEBUG = 1
passed = []
print("\n\n\n\n")
for (test_inputs, allowable_moves) in tests:
    print("")
    try:
      (game_id, turn_id)=test_inputs[0:2]
      cprint(f"TEST: {test_inputs}", "cyan")
      cprint(f"  https://play.battlesnake.com/g/{game_id}/?turn={turn_id}", "cyan")

      req = load_request(*test_inputs)
      cmd = snake.move(req)
  
      if cmd in allowable_moves:
        passed.append(test_inputs)
        cprint(f"  PASSED", "green")
      else:
        cprint(f"  FAIL: '{cmd}' is not in allowable_moves {allowable_moves}", "red")
    except Exception as e:
      print(f"TEST: {test_inputs}")
      cprint(f"  FAIL: Exception thrown: {e}", "red")
  
if len(tests) == len(passed):
  cprint(f"*** ALL TESTS PASSED ***", "green")
  sys.exit(0)
else:
  x=f"{len(tests)-len(passed)}/{len(tests)}"
  w=len(x)
  cprint(f"{'*'*(21+w)}\n*** {x} TESTS FAILED ***\n{'*'*(21+w)}", "red")
  sys.exit(1)
