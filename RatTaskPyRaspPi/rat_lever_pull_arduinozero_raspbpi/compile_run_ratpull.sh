
source env/bin/activate

g++ -o ratpull2 RatPull.cpp -lwiringPi -I/usr/include/python3.11 -lpython3.11

sudo ./ratpull2

bash