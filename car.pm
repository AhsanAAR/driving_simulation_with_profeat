mdp

const int LEFT_BOUNDARY  = -5;
const int RIGHT_BOUNDARY = 5;
const int MAX_DISTANCE   = 5;
const int NUM_LANES = RIGHT_BOUNDARY - LEFT_BOUNDARY + 1;
const double P_RESPAWN = 0.5;

module car
    x : [LEFT_BOUNDARY..RIGHT_BOUNDARY] init 0;

    [left]  x > LEFT_BOUNDARY  -> (x' = x - 1);
    [right]	x < RIGHT_BOUNDARY -> (x' = x + 1);
    [stay]	true -> (x' = x);
endmodule

module obstacle
    obs_x : [LEFT_BOUNDARY..RIGHT_BOUNDARY] init 0;
    obs_y : [-1..MAX_DISTANCE] init MAX_DISTANCE;

    [initialize] obs_y = MAX_DISTANCE -> 
        1/NUM_LANES : (obs_x' = -5) & (obs_y' = obs_y - 1) +
        1/NUM_LANES : (obs_x' = -4) & (obs_y' = obs_y - 1) +
        1/NUM_LANES : (obs_x' = -3)  & (obs_y' = obs_y - 1) +
        1/NUM_LANES : (obs_x' = -2)  & (obs_y' = obs_y - 1) +
        1/NUM_LANES : (obs_x' = -1)  & (obs_y' = obs_y - 1) +
        1/NUM_LANES : (obs_x' =  0)  & (obs_y' = obs_y - 1) +
        1/NUM_LANES : (obs_x' =  1)  & (obs_y' = obs_y - 1) +
        1/NUM_LANES : (obs_x' =  2)  & (obs_y' = obs_y - 1) +
        1/NUM_LANES : (obs_x' =  3)  & (obs_y' = obs_y - 1) +
        1/NUM_LANES : (obs_x' =  4)  & (obs_y' = obs_y - 1) +
        1/NUM_LANES : (obs_x' =  5)  & (obs_y' = obs_y - 1);

        [left]  	obs_y >= 0 & obs_y < MAX_DISTANCE -> (obs_y' = obs_y - 1);
        [right] 	obs_y >= 0 & obs_y < MAX_DISTANCE -> (obs_y' = obs_y - 1);
        [stay]  	obs_y >= 0 & obs_y < MAX_DISTANCE -> (obs_y' = obs_y - 1);

        [left]  	obs_y = -1 -> (1-P_RESPAWN) : (obs_y' = obs_y) + (P_RESPAWN) : (obs_y' = MAX_DISTANCE);
        [right] 	obs_y = -1 -> (1-P_RESPAWN) : (obs_y' = obs_y) + (P_RESPAWN) : (obs_y' = MAX_DISTANCE);
        [stay]  	obs_y = -1 -> (1-P_RESPAWN) : (obs_y' = obs_y) + (P_RESPAWN) : (obs_y' = MAX_DISTANCE);
endmodule

label "crashed" = (x = obs_x & obs_y = 0);

rewards "steps"
    [left]  true : 1;
    [right] true : 1;
    [stay]  true : 1;
endrewards