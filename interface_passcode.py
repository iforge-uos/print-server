import PySimpleGUI as sg

sg.theme("Dark Blue 12")

BUTTON_WIDTH = 6
BUTTON_HEIGHT = 3
bs = (BUTTON_WIDTH, BUTTON_HEIGHT)


def main(passcode, header="iForge 3D Print System"):
    passcode = str(passcode)
    if not passcode.isnumeric():
        raise TypeError("Passcode string must be numeric!")

    passcode_input = ""
    return_value = False

    layout = [
        [sg.Text(header, font=("Helvetica", 12))],
        [sg.Text("Please Enter Passcode", font=("Helvetica", 12))],
        [sg.Text(key="-input_display_box-", size=(26, 1), justification="center", relief=sg.RELIEF_SUNKEN)],
        # password_char="*"
        [sg.Button("1", size=bs), sg.Button("2", size=bs), sg.Button("3", size=bs)],
        [sg.Button("4", size=bs), sg.Button("5", size=bs), sg.Button("6", size=bs)],
        [sg.Button("7", size=bs), sg.Button("8", size=bs), sg.Button("9", size=bs)],
        [sg.Button("Clear", size=bs), sg.Button("0", size=bs), sg.Button("Submit", size=bs)],
        [sg.Text("", key="-output_text-", font=("Helvetica", 12))]
    ]

    window = sg.Window("Passcode",
                       element_justification="center",
                       enable_close_attempted_event=True,
                       no_titlebar=True)
    window.layout(layout)
    window.finalize()
    window.maximize()

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Do you really want to exit?') == 'Yes':
            break

        if event == "Clear":
            passcode_input = ""
        elif event in "1234567890":
            passcode_input += event
        elif event == "Submit":
            if passcode_input == passcode:
                return_value = True
                break
            else:
                window["-output_text-"]("WRONG - TRY AGAIN", text_color="red")
                passcode_input = ""

        window["-input_display_box-"]("X" * len(passcode_input))

    window.close()
    return return_value


if __name__ == "__main__":
    print(main("69420"))
