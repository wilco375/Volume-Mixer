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
1. Go to the `pc` folder, right-click on `main.py` and click 'Create shortcut'.
2. Press the keyboard shortcut Win+R and enter `shell:startup`.
3. Move the created `main.py` shortcut to the startup folder.
4. Right-click the shortcut, click 'Properties'.
5. In the 'Target' field, add ` start` after the path, so it becomes `"C:\...\pc\main.py" start`
6. Change the 'Run' field to 'Minimized'.
7. Click 'OK'.

#### Linux
1. Add a cronjob by running `crontab -e`.
2. Take note of the path of the `main.py` file in the `pc` folder. In the cronjob, insert the following line:
    `@reboot python "<path-to-volume-mixer>/pc/main.py" start &`, e.g. `@reboot python "/home/<user>/Downloads/Volume-Mixer/pc/main.py" start &`, and save it.

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
