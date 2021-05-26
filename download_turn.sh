game_id=$1
turn=$2
file=testcases/$game_id.$turn.txt
curl "https://engine.battlesnake.com/games/$game_id/frames?offset=$turn&limit=1" -o $file

cat $file
echo ""