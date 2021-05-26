import json
import string
# 
# 'turn'
# 'you.id'
# 'you.health'
# 'you.body'
# 'board.snakes'
# 'board.food'
# 'board.width'
# 'board.height'
# 
# 
# 

def recursive_lower_keys(t):
  if type(t) is dict:
    return dict((k.lower(), recursive_lower_keys(v)) for k,v in t.items())
  elif type(t) is list:
    return list(recursive_lower_keys(e) for e in t)
  else:
    return t

game_id = 'c27ec142-7d49-4843-8ccb-a8d991e7f8fe'
turn_id = 35

game_json = recursive_lower_keys(json.load(open(f"testcases/{game_id}.txt", 'r')))
turn_json = recursive_lower_keys(json.load(open(f"testcases/{game_id}.{turn_id}.txt", 'r')))

# print(f"{turn_json}")

def frame_to_snake(frame_snake):
  d = frame_snake
  d['head'] = frame_snake['body'][0]
  d['length'] = len(frame_snake['body'])
  return d
  
def frame_to_you_snake(frame):
  my_snakes = ["Evie", "Starting Snake Python"]
  name_counts = {}
  you_snake = None
  for snake in frame["snakes"]:
    name_counts[snake["name"]] = name_counts.get(snake["name"], 0) + 1
    if snake["name"] in my_snakes:
      you_snake = snake
  
  my_snake_count = sum(name_counts.get(n, 0) for n in my_snakes)
  if my_snake_count != 1:
    raise RuntimeError(f"Unable to determine 'you' snake:{name_counts}")

  return frame_to_snake(you_snake)

def game_and_frame_to_move_request(game, frame):
  return {
   "turn": frame["turn"],
   "you": frame_to_you_snake(frame),
   "board": {
     "width": game["width"],
     "height": game["height"],
     "snakes": (frame_to_snake(s) for s in frame["snakes"]),
     "food": frame["food"],
   }
  }

print(game_and_frame_to_move_request(game_json['game'], turn_json['frames'][0]))

