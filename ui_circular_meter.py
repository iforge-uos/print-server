from random import randint
import PySimpleGUI as sg

class Circular_Progressbar():

    def __init__(self, graph_bg='green', bar_radius=50, bar_width=10, gap=5,
        bar_color='yellow', progress_color='blue', text_color='white',
        text_font=('Courier New', 16)):

        self.text_font      = text_font
        self.text_color     = text_color
        self.bar_radius     = bar_radius
        self.bar_width      = bar_width
        self.bar_color      = bar_color
        self.graph_bg       = graph_bg
        self.progress_color = progress_color
        self.gap            = gap + (self.bar_width+1)//2
        self.degree         = 0
        self.target         = 0
        self.graph  = sg.Graph(
            (2*(self.bar_radius+self.gap), 2*(self.bar_radius+self.gap)),
            (-self.bar_radius-self.gap, -self.bar_radius-self.gap),
            ( self.bar_radius+self.gap,  self.bar_radius+self.gap),
            background_color=self.graph_bg)
        self.p, self.t   = None, None

    def initial(self, angle=0):
        self.graph.draw_circle((0, 0), self.bar_radius,
            line_color=self.bar_color, line_width=self.bar_width)
        angle = min(360, max(0, angle))
        self.set_now(0)
        self.set_target(0)

    def set_target(self, angle=0, step=5):
        self.target = min(360, max(0, int(angle)))
        self.step = min(360, max(1, int(step)))

    def set_now(self, angle=0):
        self.angle = min(360, max(0, int(angle)))

    def move(self):
        if self.target == self.angle:
            return True
        if self.angle < self.target:
            self.angle = min(self.target, self.angle+self.step)
        else:
            self.angle = max(self.target, self.angle-self.step)
        if self.p:
            self.graph.delete_figure(self.p)
        if self.t:
            self.graph.delete_figure(self.t)
        text = f'{self.angle/3.6:.1f}%'
        r = self.bar_radius
        if self.angle == 360:
            self.p = self.graph.draw_circle((0, 0), self.bar_radius,
                line_color=self.progress_color, line_width=self.bar_width+1)
        else:
            self.p = self.graph.draw_arc((-r, r), (r, -r), self.angle, 0,
                style='arc', arc_color=self.progress_color,
                line_width=self.bar_width+1)
        self.t = self.graph.draw_text(
            text, (0, 0), color=self.text_color, font=self.text_font,
            text_location=sg.TEXT_LOCATION_CENTER)
        return False

progress_bar = Circular_Progressbar()
layout = [[progress_bar.graph]]

window = sg.Window('Circular Progressbar', layout, finalize=True)
progress_bar.initial()
progress_bar.set_target(randint(0, 360))

while True:

    event, values = window.read(timeout=10)
    print(event)
    if event == sg.WINDOW_CLOSED:
        break
    elif event == '__TIMEOUT__':
        if progress_bar.move():
            progress_bar.set_target(randint(0, 360))

window.close()