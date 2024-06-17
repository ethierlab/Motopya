#include <CircularBuffer.h>

// DECLARATION VARIABLES------------
const int lenBuffer =  800;
CircularBuffer<int, lenBuffer> dataBuffer;
int AnalogIN = A0;
int leverVal;
int DL = 10;  // sampling freq
int DL_Sampling = 10; // buffer freq : every x ms
float valMoyenne;
float initTrial;
float baselineTrial;
int aveOnLast = 10;
float ave = 0.0;
unsigned long startArduinoProg;
unsigned long startSession;
unsigned long startTrial;
unsigned long bufferTimeFreq;
unsigned long stopTrial;
unsigned long LastTime; // le dernier temps du buffer data
int compteur = 0;
String serialCommand = "wait";
bool sendData = false;

// FONCTIONS ---------------------------------
float avebuffer(int aveOnLast) {
  // sort la moyenne des x derniers
  float ave = 0.0;
  for (int i = dataBuffer.size() - aveOnLast; i < dataBuffer.size(); i++) {
    ave += dataBuffer[i];
  }
  ave = ave / aveOnLast;
  return ave;
}


void sendData2Python() {
  // envoie les données de l'essai : sous la forme ##;##;##;...fin et
  // la forme temps correspondant en seconde ligne
  unsigned long timeStamp;
  unsigned long StartTime;
  Serial.flush();
  // Data
  for (int i = 0; i < dataBuffer.size(); i++) {
    Serial.print(dataBuffer[i]);
    Serial.print(';');
  }
  // Temps
  Serial.println("fin");  // code de fin d'envoi de données
  StartTime=LastTime-(lenBuffer* DL_Sampling);

  for (int i = 0; i < dataBuffer.size(); i++) {
    timeStamp=StartTime+(i*DL_Sampling);
    Serial.print(timeStamp);
    Serial.print(';');
  }
  Serial.println("fin");
    // code de fin d'envoi de données
}


 void fillBuffer() {
  // Rempli la pile temps et data et retourne la moyenne des n dernières valeurs data
  
  // rempli le buffer data
  leverVal = analogRead(AnalogIN);
  dataBuffer.push(leverVal); 
  
  // Prends en note le dernier temps enregistre dans le buffer
  LastTime = millis() - startArduinoProg;
  
  
}
void experimentOn(){
  
  int posIndice;
 
  // Devrait aller dans 'case i' : 
  posIndice = serialCommand.indexOf('b');
  initTrial=serialCommand.substring(1,posIndice).toFloat();
  baselineTrial=serialCommand.substring(posIndice+1).toFloat();
  while (serialCommand.charAt(0)=='s'){
  if (Serial.available() > 0) {
     serialCommand = Serial.readStringUntil('\r');
  }

  fillBuffer();
  delay(DL_Sampling);
  valMoyenne=avebuffer(aveOnLast);
  
  if (valMoyenne>initTrial){
    sendData2Python();
    
  }
  }
}

// INITIALISATION-------------------------------
void setup() {
  // put your setup code here, to run once:
  pinMode(AnalogIN, INPUT);
  pinMode(13,OUTPUT);
  // pinMode(10, OUTPUT);
  // pinMode(9,OUTPUT);
  Serial.begin(115200);  // baud rate
  startArduinoProg=millis(); // début programme
  
}

void loop() {
  
  if (Serial.available() > 0) {
    serialCommand = Serial.readStringUntil('\r');
  }
  
  switch (serialCommand.charAt(0)){ // Première lettre de la commande
    
    case 'w': // boucle defaut standby
        digitalWrite(13, LOW);
      break;
    case 'i': // Initialisation : transmission des paramètres de la tâche à partir de Python
     
      break;
    case 's': // Start
      digitalWrite(13, HIGH);
      experimentOn();
      break;
  }

  
}
