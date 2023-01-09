import gradio as gr
import SMRS
import json

title = "Multiple Interfaces"

LOGIN_FLAG = False


# global is_login
# is_login = 0

# app 1
def dummy():
    return 0


def get_cur_road_temp():
    return "1111"


def get_cur_road_hum():
    return "2222"


def get_cur_air_temp():
    return "3333"


def get_pre_heat_set_temp():
    return "4444"


def get_pos_heat_set_temp():
    return "5555"


def get_pos_heat_set_hum():
    return "6666"


def get_emer_heat_set_temp():
    return "7777"

i = 0

app1 = gr.Interface(fn=dummy, inputs=None, outputs="text")
app2 = gr.Interface(fn=dummy, inputs=None, outputs="text")
app3 = gr.Interface(fn=dummy, inputs=None, outputs="text")
app4 = gr.Interface(fn=dummy, inputs=None, outputs="text")
# app1 =  gr.Interface(fn = dummy, inputs="text", outputs="text")
# app2 =  gr.Interface(fn = dummy, inputs="text", outputs="text")
# app3 =  gr.Interface(fn = dummy, inputs="text", outputs="text")
# app4 =  gr.Interface(fn = dummy, inputs="text", outputs="text")

with gr.Blocks() as app1:
    with gr.Row():
        with gr.Column():
            gr.Markdown("""현재 환경""")
            cur_road_temp = gr.Textbox(label="현재 노면 온도")
            cur_road_hum = gr.Textbox(label="현재 노면 습도")
            cur_air_temp = gr.Textbox(label="대기 온도")
        with gr.Column():
            gr.Markdown("""설정 환경""")
            pre_heat_set_temp = gr.Textbox(label="예열 설정 온도")
            pos_heat_set_temp = gr.Textbox(label="본가동 설정 온도")
            pos_heat_set_hum = gr.Textbox(label="본가동 설정 습도")
            emer_heat_set_temp = gr.Textbox(label="비상 가동 온도")
    with gr.Row():
        gr.Markdown("현재 상태")
    with gr.Row():
        gr.Box()
        gr.Box()
        gr.Box()
    with gr.Row():
        refresh_btn = gr.Button("Refresh")
        # column 1
        refresh_btn.click(fn=get_cur_road_temp, inputs=None, outputs=cur_road_temp)
        refresh_btn.click(fn=get_cur_road_hum, inputs=None, outputs=cur_road_hum)
        refresh_btn.click(fn=get_cur_air_temp, inputs=None, outputs=cur_air_temp)
        # column 2
        refresh_btn.click(fn=get_pre_heat_set_temp, inputs=None, outputs=pre_heat_set_temp)
        refresh_btn.click(fn=get_pos_heat_set_temp, inputs=None, outputs=pos_heat_set_temp)
        refresh_btn.click(fn=get_pos_heat_set_hum, inputs=None, outputs=pos_heat_set_hum)
        refresh_btn.click(fn=get_emer_heat_set_temp, inputs=None, outputs=emer_heat_set_temp)

    def test():
        global i
        i += 1
        return i

    app1.load(test, inpupts=None, outputs=pre_heat_set_temp, every=1)



def update_value(val):
    return f'Value is set to {val}'


def pre_heat():
    widget.send_CMD(widget.btn_PRE_HEAT_ON)

    return f'pre_heat'


def pre_heat_end():
    return f'pre_heat_end'


def pre_heat_auto_change():
    return f'pre_heat_auto_change'


def pos_heat_end():
    return f'pos_heat_end'


def pos_heat_auto_change():
    return f'pos_heat_auto_change'


def pos_heat():
    widget.send_CMD(widget.btn_HEAT_ON)
    return f'pos_heat'


def auto():
    return f'auto'


def man():
    return f'man'


def end():
    return f'end'


def init_set():
    return f'init_set'


with gr.Blocks() as app2:
    with gr.Row():
        with gr.Column():
            gr.Markdown("자동 설정")
            pre_heat_set_temp = gr.Slider(0, 50, step=1, label="예열 설정 노면 온도 (℃)")
            pre_heat_dur_time = gr.Slider(0, 60, step=1, label="예열 가동 지속 시간 (Min)")
            pos_heat_set_temp = gr.Slider(0, 50, step=1, label="본 가동 설정 노면 온도 (℃)")
            pos_heat_set_hum = gr.Slider(0, 7, step=1, label="본 가동 설정 노면 습도 (Level)")
            pos_heat_dur_time = gr.Slider(0, 60, step=1, label="본 가동 지속 시간 (Min)")
            emer_heat_set_temp = gr.Slider(0, 50, step=1, label="비상 가동 대기 온도(℃)")
            md = gr.Markdown()
            # pre_heat_set_temp.change(fn=update_value,  inputs=pre_heat_set_temp , outputs=md)
            # pre_heat_dur_time.change(fn=update_value,  inputs=pre_heat_dur_time , outputs=md)
            # pos_heat_set_temp.change(fn=update_value,  inputs=pos_heat_set_temp , outputs=md)
            # pos_heat_set_hum.change(fn=update_value,   inputs=pos_heat_set_hum  , outputs=md)
            # pos_heat_dur_time.change(fn=update_value,  inputs=pos_heat_dur_time , outputs=md)
            # emer_heat_set_temp.change(fn=update_value, inputs=emer_heat_set_temp, outputs=md)
            pre_heat_btn = gr.Button("강제 예열 가동")
            pos_heat_btn = gr.Button("강제 본 가동")
            pre_heat_btn.click(fn=pre_heat, inputs=None, outputs=md)
            pos_heat_btn.click(fn=pos_heat, inputs=None, outputs=md)
        with gr.Column():
            gr.Markdown("수동 설정")
            pre_heat_dur_time = gr.Slider(0, 60, step=1, label="예열 가동 지속 시간 (Min)")
            pre_heat_end_btn = gr.Button("예열 가동 후 종료")
            pre_heat_end_btn.click(fn=pre_heat_end, inputs=None, outputs=md)
            pre_heat_auto_change_btn = gr.Button("예열 가동 후 자동 전환")
            pre_heat_auto_change_btn.click(fn=pre_heat_auto_change, inputs=None, outputs=md)
            pos_heat_dur_time = gr.Slider(0, 60, step=1, label="본 가동 지속 시간 (Min)")
            pos_heat_end_btn = gr.Button("본 가동 후 종료")
            pos_heat_end_btn.click(fn=pos_heat_end, inputs=None, outputs=md)
            pos_heat_auto_change_btn = gr.Button("본 가동 후 자동 전환")
            pos_heat_auto_change_btn.click(fn=pos_heat_auto_change, inputs=None, outputs=md)
    with gr.Row():
        gr.Markdown("Main 설정")
    with gr.Row():
        auto_btn = gr.Button("자동")
        auto_btn.click(fn=auto, inputs=None, outputs=md)
        man_btn = gr.Button("수동")
        man_btn.click(fn=man, inputs=None, outputs=md)
        end_btn = gr.Button("종료")
        end_btn.click(fn=end, inputs=None, outputs=md)
    with gr.Row():
        init_set_btn = gr.Button("설정초기화")
        init_set_btn.click(fn=init_set, inputs=None, outputs=md)


def take_picture():
    return f'take_picture'


with gr.Blocks() as app3:
    md = gr.Markdown()
    with gr.Row():
        gr.Image("logo1.png")
    with gr.Row():
        take_picture_btn = gr.Button("사진 촬영")
        take_picture_btn.click(fn=take_picture, inputs=None, outputs=md)

with gr.Blocks() as app4:
    with gr.Row():
        gr.Dataframe(type="numpy", datatype="number", row_count=5, col_count=3)


# def login_send():
#     is_login = 1
#     return f'login_send'
#
#
# with gr.Blocks() as app0:
#     with gr.Row():
#         md = gr.Markdown()
#         login_id = gr.Textbox(label="아이디")
#         login_pw = gr.Textbox(label="패스워드")
#         login_btn = gr.Button("로그인")
#         login_btn.click(fn=login_send, inputs=None, outputs=md)
#
# login = gr.TabbedInterface([app0], ["로그인"])
# login.launch()
#
# while (is_login == 0):
#     if is_login == 1:
#         login.close()
#         break
def check_auth_mongodb(username, password):
    global LOGIN_FLAG
    saved_passwd = SMRS.signup_col.find_one({'id': username})['pwd']

    if saved_passwd == password:
        print('password is correct!!')
        if not LOGIN_FLAG:
            widget.initMqtt(username, on_message_sp, on_message_cb=on_message_sp_rcv)
            LOGIN_FLAG = True
        return True
    else:
        return False

def check_auth(username, password):
    if username == "user1" and password == "123":
        return True
    else:
        return False

def on_message_sp_rcv(client, userdata, message):
    print('rcv function')
    rcvData = message.payload.decode("utf-8")
    on_message_sp(rcvData, message.topic)

def on_message_sp(msg, topic):
    jsonData = json.loads(msg)
    print('on_message_callback: ', msg)
    if topic == SMRS.sub_root_topic + 'STATUS':
        print("CMD: ", "CH1: ", str(jsonData['CH1']))
        print("CMD: ", "CH2: ", str(jsonData['CH2']))

        if jsonData['CH1'] == True and jsonData[ 'CH2'] == True:
            return

        if jsonData['CH1'] == True:  # PRE HEAT ON
            print("PRE HEAT: ON")
            #TODO: '강제 예열 가동' 버튼 -> YELLOW color
        elif jsonData['CH1'] == False:  # PRE HEAT OFF
            print("PRE HEAT: OFF")
            #TODO: '강제 예열 가동' 버튼 -> GRAY color

        if jsonData['CH2'] == True:  # HEAT ON
            print("HEAT: ON")
            #TODO: '강제 본 가동' 버튼 -> PINK color
        elif jsonData['CH2'] == False:  # HEAT OFF
            print("HEAT: OFF")
            #TODO: '강제 본 가동' 버튼 -> GRAY color

        if jsonData['CH1'] == False and jsonData[ 'CH2'] == False:
            print("PRE HEAT: OFF")
            print("HEAT: OFF")
            # self.flag_HEAT_ON = False

        """
        self.config_dict = {
            'pre_heat_road_temp':   3,
            'heat_road_temp':       1,
            'set_road_humidity':    3,
            'set_air_temp':         -15,
            'pre_heat_on_time':     60,
            'heat_on_time':         90,
            'road_temp':            0,
            'road_humidity':        0,
            'air_temp':             0
        }
        """

    elif topic == SMRS.sub_root_topic + 'CONFIG':
        print('received CONFIG')
        for key, value in jsonData.items():
            print(key, value)
            # TODO:
            # display the value
            if key == 'pre_heat_road_temp':
                pre_heat_set_temp = value

    elif topic == SMRS.sub_root_topic + 'IMAGE':
        print('image captured')

widget = SMRS.run(pc_app = False)
# password = widget.util_func.read_var('enerpia_1')
# print(password)

smrs = gr.TabbedInterface([app1, app2, app3, app4], ["현재상태", "설정", "카메라", "로그"])
# smrs.launch(auth=check_auth, auth_message="Please Enter ID and Password")
smrs.launch(auth=check_auth_mongodb, auth_message="Please Enter ID and Password", 
            server_name='192.168.0.26', server_port=7860, enable_queue=True)
# demo.launch(share=True)
