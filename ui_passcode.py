import PySimpleGUI as sg

sg.theme("Dark Blue 12")

BUTTON_WIDTH = 6
BUTTON_HEIGHT = 4
bs = (BUTTON_WIDTH, BUTTON_HEIGHT)


def main(passcode, header="iForge 3D Print System", quitcode=42069):
    passcode = str(passcode)
    quitcode = str(quitcode)
    if not passcode.isnumeric():
        raise TypeError("Passcode string must be numeric!")

    passcode_input = ""
    return_value = False

    layout = [
        [sg.VStretch()],
        [sg.VStretch()],
        [sg.Text(header)],
        [sg.VStretch()],
        [sg.Text("Please Enter Passcode")],
        [sg.Text(key="-input_display_box-", size=(26, 1), justification="center", relief=sg.RELIEF_SUNKEN)],
        # password_char="*"
        [sg.Button("1", size=bs), sg.Button("2", size=bs), sg.Button("3", size=bs)],
        [sg.Button("4", size=bs), sg.Button("5", size=bs), sg.Button("6", size=bs)],
        [sg.Button("7", size=bs), sg.Button("8", size=bs), sg.Button("9", size=bs)],
        [sg.Button("Clear", size=bs), sg.Button("0", size=bs), sg.Button("Submit", size=bs)],
        [sg.VStretch()],
        [sg.Text("", key="-output_text-")],
        [sg.VStretch()],
        [sg.VStretch()]
    ]

    window = sg.Window("Passcode",
                       element_justification="center",
                       enable_close_attempted_event=True,
                       resizable=True)
    window.layout(layout)
    window.finalize()
    window.maximize()

    while True:
        window.bring_to_front()
        event, values = window.read(timeout=1000)

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
                if passcode_input == quitcode:
                    exit(0)

                window["-output_text-"]("WRONG - TRY AGAIN", text_color="red")
                passcode_input = ""

        window["-input_display_box-"]("X" * len(passcode_input))

    window.close()
    return return_value


if __name__ == "__main__":
    print(main("69420"))
