import gradio as gr
import SMRS
import json
import time
import base64
import numpy as np
import cv2

title = "Multiple Interfaces"

LOGIN_FLAG = False

g_pre_heat_road_temp    = 0
g_heat_road_temp        = 0
g_set_road_humidity     = 0
g_set_air_temp          = 0
g_pre_heat_on_time      = 0
g_heat_on_time          = 0
g_road_temp             = 0
g_road_humidity         = 0
g_air_temp              = 0

g_l_pre_heat            = 0
g_l_heat                = 0
g_l_emc_heat            = 0

label_dict = {  'label_pre_heat_on': 'gray',
                'label_heat_on': 'gray',
                'label_emc_heat_on': 'gray',
                'btn_AUTO_MODE': 'gray'}

jpg_original = None
capture_flag = False

# global is_login
# is_login = 0

# app 1
def dummy():
    return 0

def update_pre_heat_set_temp(value):
    widget.LineEdit_pre_heat_road_temp_RET(value)

def update_pre_heat_dur_time(value):
    widget.LineEdit_pre_heat_on_time_RET(value)

def update_pos_heat_set_temp(value):
    widget.LineEdit_heat_road_temp_RET(value)

def update_pos_heat_set_hum(value):
    widget.LineEdit_set_road_humidity_RET(value)

def update_pos_heat_dur_time(value):
    widget.LineEdit_heat_on_time_RET(value)

def update_emer_heat_set_temp(value):
    widget.LineEdit_set_air_temp_RET(value)


def fn_pre_heat_set_temp():
    return g_pre_heat_road_temp

def fn_pre_heat_dur_time():
    return g_pre_heat_on_time

def fn_pos_heat_set_temp():
    return g_heat_road_temp

def fn_pos_heat_set_hum():
    return g_set_road_humidity

def fn_pos_heat_dur_time():
    return g_heat_on_time

def fn_emer_heat_set_temp():
    return g_set_air_temp

def fn_road_temp():
    return g_road_temp

def fn_road_humidity():
    return g_road_humidity

def fn_air_temp():
    return g_air_temp

def fn_update_label_1():
    return gr.Label.update(color=label_dict['label_pre_heat_on'])

def fn_update_label_2():
    return gr.Label.update(color=label_dict['label_heat_on'])

def fn_update_label_3():
    return gr.Label.update(color=label_dict['label_emc_heat_on'])

def fn_update_label_4():
    return gr.Label.update(color=label_dict['btn_AUTO_MODE'])

def fn_update_image():
    global jpg_original
    return gr.Image(jpg_original)


app1 = gr.Interface(fn=dummy, inputs=None, outputs="text")
app2 = gr.Interface(fn=dummy, inputs=None, outputs="text")
app3 = gr.Interface(fn=dummy, inputs=None, outputs="text")
# app4 = gr.Interface(fn=dummy, inputs=None, outputs="text")

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
        label_4 = gr.Label("자동")
        label_1 = gr.Label("예열 가동 중")
        label_2 = gr.Label("본 가동 중")
        label_3 = gr.Label("비상 가동 중")

    app1.load(fn_road_temp,             inputs=None, outputs=cur_road_temp,         every=1)
    app1.load(fn_road_humidity,         inputs=None, outputs=cur_road_hum,          every=1)
    app1.load(fn_air_temp,              inputs=None, outputs=cur_air_temp,          every=1)

    app1.load(fn_pre_heat_set_temp,     inputs=None, outputs=pre_heat_set_temp,     every=1)
    app1.load(fn_pos_heat_set_temp,     inputs=None, outputs=pos_heat_set_temp,     every=1)
    app1.load(fn_pos_heat_set_hum,      inputs=None, outputs=pos_heat_set_hum,      every=1)
    app1.load(fn_emer_heat_set_temp,    inputs=None, outputs=emer_heat_set_temp,    every=1)

    app1.load(fn_update_label_1,        inputs=None, outputs=label_1,               every=1)
    app1.load(fn_update_label_2,        inputs=None, outputs=label_2,               every=1)
    app1.load(fn_update_label_3,        inputs=None, outputs=label_3,               every=1)
    app1.load(fn_update_label_4,        inputs=None, outputs=label_4,               every=1)

def update_value(val):
    return f'Value is set to {val}'


def pre_heat_end():
    widget.pressed_button(widget.btn_PRE_HEAT_ON_AND_STOP)
    return f'예열 가동 후 정지'


def pre_heat_auto_change():
    widget.pressed_button(widget.btn_PRE_HEAT_ON)
    return f'예열 가동 후 자동 전환'


def pos_heat_end():
    widget.pressed_button(widget.btn_HEAT_ON_AND_STOP)
    return f'본 가동 후 정지'


def pos_heat_auto_change():
    widget.pressed_button(widget.btn_HEAT_ON)
    return f'본 가동 후 자동 전환'


def auto():
    widget.pressed_button(widget.btn_AUTO_MODE)
    return f'자동'


def end():
    widget.pressed_button(widget.btn_HEAT_STOP)
    return f'정지'


def init_set():
    widget.pressed_button(widget.btn_INIT_MODE)
    return f'설정 초기화'


with gr.Blocks() as app2:
    with gr.Row():
        """
        with gr.Column():
            gr.Markdown("자동 설정")

            with gr.Row():
                with gr.Column(scale=1, min_width=70):
                    l_pre_heat_set_temp = gr.Textbox(label="")
                with gr.Column(scale=10):
                    s_pre_heat_set_temp = gr.Slider(0, 10, step=1, label="[설정] 예열 설정 노면 온도")
                app2.load(fn_pre_heat_set_temp,  inpupts=None, outputs=l_pre_heat_set_temp,  every=1)

            with gr.Row():
                with gr.Column(scale=1, min_width=70):
                    l_pre_heat_dur_time = gr.Textbox(label="")
                with gr.Column(scale=10):
                    s_pre_heat_dur_time = gr.Slider(1, 6, step=1, label="[설정] 예열 가동 지속 횟수 (회)")
                app2.load(fn_pre_heat_dur_time,  inpupts=None, outputs=l_pre_heat_dur_time,  every=1)

            with gr.Row():
                with gr.Column(scale=1, min_width=70):
                    l_pos_heat_set_temp = gr.Textbox(label="")
                with gr.Column(scale=10):
                    s_pos_heat_set_temp = gr.Slider(-10, 10, step=1, label="[설정] 본 가동 설정 노면 온도 (℃)")
                app2.load(fn_pos_heat_set_temp,  inpupts=None, outputs=l_pos_heat_set_temp,  every=1)

            with gr.Row():
                with gr.Column(scale=1, min_width=70):
                    l_pos_heat_set_hum = gr.Textbox(label="")
                with gr.Column(scale=10):
                    s_pos_heat_set_hum = gr.Slider(0, 9, step=1, label="[설정] 본 가동 설정 노면 습도 (Lev)")
                app2.load(fn_pos_heat_set_hum,  inpupts=None, outputs=l_pos_heat_set_hum,  every=1)

            with gr.Row():
                with gr.Column(scale=1, min_width=70):
                    l_pos_heat_dur_time = gr.Textbox(label="")
                with gr.Column(scale=10):
                    s_pos_heat_dur_time = gr.Slider(1, 4, step=1, label="[설정] 본 가동 지속 횟수 (회)")
                app2.load(fn_pos_heat_dur_time,  inpupts=None, outputs=l_pos_heat_dur_time,  every=1)

            with gr.Row():
                with gr.Column(scale=1, min_width=70):
                    l_emer_heat_set_temp = gr.Textbox(label="")
                with gr.Column(scale=10):
                    s_emer_heat_set_temp = gr.Slider(-30, 20, step=1, label="[설정] 비상 가동 대기 온도(℃)")
                app2.load(fn_emer_heat_set_temp,  inpupts=None, outputs=l_emer_heat_set_temp,  every=1)


            s_pre_heat_set_temp.change(fn=update_pre_heat_set_temp,  inputs=s_pre_heat_set_temp,  outputs=None)
            s_pre_heat_dur_time.change(fn=update_pre_heat_dur_time,  inputs=s_pre_heat_dur_time,  outputs=None)
            s_pos_heat_set_temp.change(fn=update_pos_heat_set_temp,  inputs=s_pos_heat_set_temp,  outputs=None)
            s_pos_heat_set_hum.change(fn=update_pos_heat_set_hum,    inputs=s_pos_heat_set_hum,   outputs=None)
            s_pos_heat_dur_time.change(fn=update_pos_heat_dur_time,  inputs=s_pos_heat_dur_time,  outputs=None)
            s_emer_heat_set_temp.change(fn=update_emer_heat_set_temp,inputs=s_emer_heat_set_temp, outputs=None)

            md = gr.Markdown()
        """

        with gr.Column():
            gr.Markdown("예열가동 설정")
            md = gr.Markdown()
            pre_heat_end_btn = gr.Button("예열 가동 후 정지")
            pre_heat_end_btn.click(fn=pre_heat_end, inputs=None, outputs=md)
            pre_heat_auto_change_btn = gr.Button("예열 가동 후 자동 전환")
            pre_heat_auto_change_btn.click(fn=pre_heat_auto_change, inputs=None, outputs=md)

        with gr.Column():
            gr.Markdown("본가동 설정")
            md = gr.Markdown()
            # ll_pre_heat_dur_time = gr.Textbox(label="")
            # app2.load(fn_pre_heat_dur_time,  inpupts=None, outputs=ll_pre_heat_dur_time,  every=1)

            # pre_heat_end_btn = gr.Button("예열 가동 후 정지")
            # pre_heat_end_btn.click(fn=pre_heat_end, inputs=None, outputs=md)
            # pre_heat_auto_change_btn = gr.Button("예열 가동 후 자동 전환")
            # pre_heat_auto_change_btn.click(fn=pre_heat_auto_change, inputs=None, outputs=md)

            # ll_pos_heat_dur_time = gr.Textbox(label="")
            # app2.load(fn_pos_heat_dur_time,  inpupts=None, outputs=ll_pos_heat_dur_time,  every=1)
            pos_heat_end_btn = gr.Button("본 가동 후 정지")
            pos_heat_end_btn.click(fn=pos_heat_end, inputs=None, outputs=md)
            pos_heat_auto_change_btn = gr.Button("본 가동 후 자동 전환")
            pos_heat_auto_change_btn.click(fn=pos_heat_auto_change, inputs=None, outputs=md)

    with gr.Row():
        gr.Markdown("Main 설정")
        md = gr.Markdown()

    with gr.Row():
        auto_btn = gr.Button("자동")
        auto_btn.click(fn=auto, inputs=None, outputs=md)
        end_btn = gr.Button("정지")
        end_btn.click(fn=end, inputs=None, outputs=md)
        init_set_btn = gr.Button("설정초기화")
        init_set_btn.click(fn=init_set, inputs=None, outputs=md)


def take_picture():
    global capture_flag, jpg_original
    widget.pressed_button(widget.btn_capture)
    count = 0
    while(True):
        if capture_flag: 
            break
        else:
            time.sleep(0.5)
            count+=1
            if (count == 5): 
                break

    capture_flag = False
    return jpg_original
    return f'take_picture'


with gr.Blocks() as app3:
    md = gr.Markdown()
    with gr.Row():
        # gr.Image("./icon/logo1.png")
        img_output = gr.Image("./icon/logo1.png")
        # outputs = gr.outputs.Image(type="numpy", label = "capture image")

    app3.load(fn_update_image,        inputs=None, outputs=img_output,               every=1)

    with gr.Row():
        take_picture_btn = gr.Button("사진 촬영")
        # take_picture_btn.click(fn=take_picture, inputs=None, outputs=md)
        take_picture_btn.click(fn=take_picture, inputs=None, outputs=img_output)

with gr.Blocks() as app4:
    with gr.Row():
        gr.Dataframe(type="numpy", datatype="number", row_count=5, col_count=3)


def check_auth_mongodb(username, password):
    global LOGIN_FLAG
    if not LOGIN_FLAG:
        widget.initMqtt(username, on_message_sp, on_message_cb=on_message_sp_rcv)
    SMRS.DEVICE_ID = username
    SMRS.initMongoDB()
    saved_passwd = SMRS.mongodb_signup_col.find_one({'id': username})['pwd']

    if saved_passwd == password:
        print('password is correct!!')
        if not LOGIN_FLAG:
            # widget.initMqtt(username, on_message_sp, on_message_cb=on_message_sp_rcv)
            widget.send_CMD('INIT')
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
    global g_pre_heat_road_temp
    global g_heat_road_temp    
    global g_set_road_humidity
    global g_set_air_temp     
    global g_pre_heat_on_time
    global g_heat_on_time   
    global g_road_temp     
    global g_road_humidity 
    global g_air_temp     
    global g_l_pre_heat

    jsonData = json.loads(msg)
    # print('on_message_callback: ', msg)

    if topic == SMRS.sub_root_topic + 'DATA':
        roadTemp = jsonData['road_temp']
        roadHumidity = jsonData['road_humidity']
        airTemp = jsonData['air_temp']

    elif topic == SMRS.sub_root_topic + 'CONFIG':
        print('received CONFIG')
        for key, value in jsonData.items():
            print(key, value)
            # TODO:
            # display the value
            if key == 'pre_heat_road_temp':
                g_pre_heat_road_temp = value
            elif key == 'heat_road_temp':
                g_heat_road_temp = value
            elif key == 'set_road_humidity':
                g_set_road_humidity= value
            elif key == 'set_air_temp':
                g_set_air_temp = value
            elif key == 'pre_heat_on_time':
                g_pre_heat_on_time = value
            elif key == 'heat_on_time':
                g_heat_on_time = value
            elif key == 'road_temp':
                g_road_temp = value
            elif key == 'road_humidity':
                g_road_humidity = value
            elif key == 'air_temp':
                g_air_temp = value

    elif topic == SMRS.sub_root_topic + 'IMAGE':
        global jpg_original, capture_flag
        print('image captured')
        filename = jsonData['filename'].split('/')[2]
        img_str = jsonData['IMG']

        # to decode back to np.array
        jpg_original = base64.b64decode(img_str)
        jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
        # decoded_img = cv2.imdecode(jpg_as_np, flags=1)
        jpg_original = cv2.imdecode(jpg_as_np, flags=1)
        jpg_original = cv2.cvtColor(jpg_original, cv2.COLOR_BGR2RGB)

        capture_flag = True

        # filename = jsonData['filename']
        # cv2.imwrite(filename, decoded_img)
        # print('image saved')

        # self.update_image(decoded_img, 480, 360)
        # self.btn_capture.setStyleSheet("background-color: gray; border: 1px solid black")
        # self.textEdit.append('captured ' + filename)

    elif topic == SMRS.sub_root_topic + 'BUTTON':
        print(jsonData['btn'][0][4:], ': ', jsonData['btn'][1])
        if jsonData['btn'][1] != '#808080' and jsonData['btn'][1] != 'gray':
        # if jsonData['btn'][1] in ['blue', 'pink', 'yellow']:
            time_text = time.strftime('%y.%m.%d_%H:%M:%S', time.localtime(time.time()))
            log_text = time_text + '   ' + jsonData['btn'][0][4:]
            # self.textEdit_log.append(log_text)
            # TODO: write log
            print(log_text)
        
        if jsonData['btn'][0] == 'btn_AUTO_MODE':
            label_dict[jsonData['btn'][0]] = jsonData['btn'][1]

        # self.findChild(QPushButton, jsonData['btn'][0]).setStyleSheet("background-color: {}".format(jsonData['btn'][1]))
        # TODO: change button color

    elif topic == SMRS.sub_root_topic + 'LABEL':
        # self.findChild(QLabel, jsonData['label'][0]).setStyleSheet("background-color: {}".format(jsonData['label'][1]))
        # TODO: change label color
        print(jsonData['label'][0][6:], ': ', jsonData['label'][1])
        label_dict[jsonData['label'][0]] = jsonData['label'][1]

        if jsonData['label'][0] == 'label_emc_heat_on':
            time_text = time.strftime('%y.%m.%d_%H:%M:%S', time.localtime(time.time()))
            log_text = time_text + '   ' + 'EMC_HEAT_ON'
            # self.textEdit_log.append(log_text)
            # TODO: write log
            print(log_text)
            

widget = SMRS.run(pc_app = False)
# password = widget.util_func.read_var('enerpia_1')
# print(password)

# smrs = gr.TabbedInterface([app1, app2, app3, app4], ["현재상태", "설정", "카메라", "로그"])
smrs = gr.TabbedInterface([app1, app2, app3], ["현재상태", "설정", "카메라"])
# smrs.launch(auth=check_auth, auth_message="Please Enter ID and Password")
smrs.launch(auth=check_auth_mongodb, auth_message="Please Enter ID and Password", 
            server_name='192.168.0.26', server_port=7860, enable_queue=True)
# demo.launch(share=True)
