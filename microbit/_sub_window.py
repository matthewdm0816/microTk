__doc__ = '''sub-windows called by main screen thread
all functions act like below:
def func():
    initialize()
    while 1:
        assert func.running
        update_once()
where func.running is controlled outside

contains nothing accessible
'''

__all__ = ['pin_info', 'beeper', 'rotation']
from tkinter import *
from ._hardware import _pin, spatial


# a 2-column table showing all accessible pins' status
def pin_info():
    info_width = 45

    # init
    sub = Tk()
    sub.title('Pin Status')
    sub.resizable(0, 0)
    Label(sub, text='Name').grid(row=0, column=0)
    Label(sub, text='-- Status --', width=info_width).grid(row=0, column=2)

    # layout
    curr_row = 1
    rows = []
    for i in range(len(_pin.pins)):
        pin = _pin.pins[i]
        if pin:
            Label(sub, text='pin%d' % i).grid(row=curr_row, column=0)
            Label(sub, text='|').grid(row=curr_row, column=1)
            stat = Label(sub)
            rows.append((pin, stat))
            stat.grid(row=curr_row, column=2, sticky=W)
            curr_row += 1

    # mainloop
    while 1:
        for pin, stat in rows:
            # occupied pins
            if pin.id == 12:
                stat.config(text='Reserved pin')
            elif pin.id in (5, 11):
                stat.config(text='Occupied by button %s' % 'AB' [pin.id == 11])
            elif pin.id in (3, 4, 6, 7, 9, 10) and _pin.screen_mode:
                stat.config(text='Occupied by LED screen')

            # IO pins
            else:
                time_format = lambda x: '%d mus' % x if x < 1000 else '%s ms' % (x / 1000)
                if pin.volt > 0:
                    info = 'Output : '
                    if pin.volt == 1023:
                        info += 'ONE (digital)'
                    else:
                        info += '%d (analog); PWM cycle period: %s' % (
                            pin.volt, time_format(pin.period))
                elif pin.volt_r > 0:
                    info = 'Input : '
                    if pin.volt_r == 1023:
                        info += 'ONE (digital)'
                    else:
                        info += '%d (analog); PWM cycle period: %s' % (
                            pin.volt_r, time_format(pin.period_r))
                else:
                    info = 'spare'

                stat.config(text=info)

        assert pin_info.running
        sub.update()


# a beeper
def beeper():

    # init
    sub = Tk()
    sub.title('Beeper')
    sub.resizable(0, 0)

    # layout
    Label(sub, text='Pin connected:', anchor=W).pack(fill=X)
    pin_select = IntVar(sub, value=0)
    cur_pin_id = 0
    pin_group = Frame(sub)
    pin_group.pack(fill=X)
    Radiobutton(
        pin_group, variable=pin_select, text='none', value=-1).pack(side=LEFT)
    for i in [0,1,2,8]:
        Radiobutton(
            pin_group, variable=pin_select, text='pin%d' % i,
            value=i).pack(side=LEFT)

    # mainloop
    while 1:
        assert beeper.running
        pin_id = pin_select.get()
        _pin.music_pin = _pin.pins[pin_id] if pin_id >= 0 else None
        sub.update()


# spatial rotation control for accelerometer
def rotation():
    sub = Tk()
    sub.title('Spatial rotation')
    cv = Canvas(sub, width=400, height=400, bg='#66ccff')
    cv.pack()

    # draw gravity arrow
    cv.create_line(374, 20, 386, 32)
    cv.create_line(386, 20, 374, 32)
    cv.create_text(380, 10, text='gravity')
    cv.create_text(400, 40, text='pointed\ninto screen',anchor=NE,justify=RIGHT)

    # initialize axis
    def get_axis_ends():
        for i in range(3):
            yield (axis_origin[0] + axis_l * spatial.r_matrix[i][0],
                   axis_origin[1] + axis_l * spatial.r_matrix[i][1])

    axis_origin = (50, 50)
    axis_l = 70
    axis_ends = tuple(get_axis_ends())
    axis = [cv.create_line(*axis_origin, *end) for end in axis_ends]
    text = [
        cv.create_text(*end, text=symbol, anchor='center')
        for end, symbol in zip(axis_ends, ['X', 'Y', 'front'])
    ]

    # initialize body
    def get_point_pos(px, py):
        x, y, z = (px * spatial.r_matrix[0][i] + py * spatial.r_matrix[1][i]
                   for i in range(3))
        resize = 300 / (300 - z)
        return body_origin[0] + x * resize, body_origin[1] + y * resize

    body_origin = (200, 200)
    body_w, body_h = 100, 80
    body_sketch = ((-body_w, -body_h), (body_w, -body_h), (body_w, body_h),
                   (-body_w, body_h))
    body = cv.create_polygon(
        *(get_point_pos(px, py) for px, py in body_sketch),
        outline='black',
        fill='gray' if spatial.r_matrix[2][2] < 0 else 'orange')

    # control spatial angle
    def drag_event(e):
        x = e.x - sub.winfo_width() / 2
        y = e.y - sub.winfo_height() / 2
        spatial.r_matrix = spatial.rotatey(x * 0.01) * spatial.rotatex(
            -y * 0.01) * spatial.def_matrix

    cv.bind('<B1-Motion>', drag_event)

    while 1:
        # update axis
        axis_ends = tuple(get_axis_ends())
        for i in range(3):
            cv.coords(axis[i], *axis_origin, *axis_ends[i])
            if spatial.r_matrix[i][2] > 0:
                cv.itemconfig(axis[i], dash='')
            else:
                cv.itemconfig(axis[i], dash=(4, 4))
            cv.coords(text[i], *axis_ends[i])

        # update body
        coords = []
        for pt in body_sketch:
            coords.extend(get_point_pos(*pt))
        cv.coords(body, *coords)
        cv.itemconfig(
            body, fill='gray' if spatial.r_matrix[2][2] < 0 else 'orange')

        sub.update()