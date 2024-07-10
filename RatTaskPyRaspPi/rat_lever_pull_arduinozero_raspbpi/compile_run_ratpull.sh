
source env/bin/activate

g++ -o RatPull RatPull.cpp -lwiringPi -I/usr/include/python3.11 -lpython3.11

sudo ./RatPull

bash