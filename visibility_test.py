import PySimpleGUI as sg
import copy

layout_1 = [[sg.VStretch()], [sg.Stretch(), sg.Text("layout 1"), sg.Stretch()], [sg.VStretch()]]
layout_2 = [[sg.VStretch()], [sg.Stretch(), sg.Text("layout 2"), sg.Stretch()], [sg.VStretch()]]

layout = [[sg.pin(sg.Frame(title="Frame 1", layout=copy.deepcopy(layout_1), key="fa1")),
           sg.pin(sg.Frame(title="Frame 1", layout=copy.deepcopy(layout_2), key="fa2", visible=False)),
           sg.pin(sg.Frame(title="Frame 2", layout=copy.deepcopy(layout_1), key="fb1", visible=False)),
           sg.pin(sg.Frame(title="Frame 2", layout=copy.deepcopy(layout_2), key="fb2"))]]

window = sg.Window("Test window", layout, resizable=False, return_keyboard_events=True)
window.finalize()

while True:
    event, values = window.read()

    print(event)

    if event == sg.WIN_CLOSED:
        break

    if event == "1:10":
        window["fa1"].update(visible=True)
        window["fa2"].update(visible=False)

    if event == "2:11":
        window["fa1"].update(visible=False)
        window["fa2"].update(visible=True)