game_id=$1
turn=$2
game_file=testcases/$game_id.txt
turn_file=testcases/$game_id.$turn.txt
curl "https://engine.battlesnake.com/games/$game_id" -o $game_file
curl "https://engine.battlesnake.com/games/$game_id/frames?offset=$turn&limit=1" -o $turn_file

cat $turn_file
cat $game_file
echo ""
