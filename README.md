# Volume mixer
The volume mixer device allows one to adjust the master volume and the volume of two applications at the turn of a knob.

![Device](device.jpg)

## PC side
### Prerequisites
Make sure Python and pip are installed.

Currently, only Windows PCs and (Linux) PCs using PulseAudio are supported.

### Setup
1. [Download](https://github.com/wilco375/Volume-Mixer/archive/refs/heads/master.zip) this repository and extract the zip archive.
2. Go to the `pc` folder
3. Run the command `pip install -r requirements.txt`

### Running
The program can be executed by running `python main.py`.  
The program has three modes:  
`python main.py list-applications`: show a list running programs and their volumes, which can be useful when editing the config file  
`python main.py list-devices`: list all found serial devices  
`python main.py start`: start communication with the device

Details of the commands can be viewed by adding `--help`

### Configuration
The applications displayed on the mixer device can be further configured in the `config.yaml` file. 
If this does not exist yet, copy `config.example.yaml`. The example config file contains comments describing each option. 

### Autostart
#### Windows
1. Press the keyboard shortcut Win+R and enter `shell:startup`.
2. In the folder that opens, create a `volume-mixer.bat` file.
3. Open the `volume-mixer.bat` file in a text editor (e.g. notepad).
4. Take note of the path of the `main.py` file in the `pc` folder. In the bat file, insert the following line:
    `python "<path-to-volume-mixer>\pc\main.py"`, e.g. `python "C:\Users\<user>\Downloads\Volume-Mixer\pc\main.py"`.
5. Save the file and close it.

#### Linux
1. Add a cronjob by running `crontab -e`.
2. Take note of the path of the `main.py` file in the `pc` folder. In the cronjob, insert the following line:
    `@reboot python "<path-to-volume-mixer>/pc/main.py" &`, e.g. `@reboot python "/home/<user>/Downloads/Volume-Mixer/pc/main.py" &`, and save it.

## Device side
### Prerequisites
Install Arduino IDE, and the RotaryEncoder and ezButton libraries within the Arduino IDE.

###  Pinout
| Pin | Function |
| --- | -------- |
| 2  | Display D7 |
| 3  | Display D6 |
| 4  | Display D5 |
| 5  | Display D4 |
| 6  | Rotary Encoder 1 Button |
| 7  | Rotary Encoder 2 Button |
| 8  | Rotary Encoder 3 Button |
| 11 | Display EN |
| 12 | Display RS |
| A0 | Rotary Encoder 1 A |
| A1 | Rotary Encoder 1 B |
| A2 | Rotary Encoder 2 A |
| A3 | Rotary Encoder 2 B |
| A4 | Rotary Encoder 3 A |
| A5 | Rotary Encoder 3 B |

### Setup
Simply upload the sketch in the `device` folder to the Arduino nano.
