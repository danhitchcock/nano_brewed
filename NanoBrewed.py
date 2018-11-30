import time
from kivy.app import App
from kivy.uix.label import Label
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.utils import rgba
from functools import partial
from io import BytesIO
from kivy.config import Config
from rpc_bindings import open_account, generate_account, generate_qr, nano_to_raw, receive_all, send_all, check_balance

# this file will contain your account name. I left it intentionally missing from the repo
with open('my_account.txt') as f:
    for line in f:
        my_account = line
"""
# houses the transaction history from the kivy app. It's crude and unencrypted.
with open('transaction_history.txt', 'r') as f:
    accounts = []
    keys = []
    for i, line in enumerate(f):
        # print(i, line)
        if i % 2 == 0:
            accounts.append(line.replace(' ', '').replace('\n', ''))
        else:
            keys.append(line.replace(' ', '').replace('\n', ''))

# open accounts or receive from transaction history
for account, key in zip(accounts, keys):
    try:
        hash = open_account(account, key)
        if hash == "Previous block exists. Use receive.":
            pass
        else:
            print('%s opened'%account)
    except:
        pass
        # print('nothing to open for %s' % account)
    try:
        received = receive_all(account, key)
        if received !="No Pending Transactions.":
            print('%s received'%account)
    except:
        # print('nothing to receive for %s' % account)
        pass

# send all nanos back to your wallet in 'my_account.txt'
for account, key in zip(accounts, keys):
    try:
        sent = send_all(account, key, my_account)
        if sent:
            print('%s sent to %s'%(account, my_account))
        else:
            pass
    except:
        pass
        #print('nothing to send for %s' % account)
"""
# the beers. has beer information and keg information
# the tap number will determine which flow_meter to use
# the valve number controls whichever valve
beer_list = {
    1: {
        "Tap Number": 1,
        "Valve Number": 1,
        "Name": "DANTOBERFEST".upper(),
        "Style": "MOCKTOBERFEST ALE".upper(),
        "IBU": 22,
        "SRM": 9,
        "ABV": 8.5,
        "FG": 1.012,
        "Hops": "Hallertauer".upper(),
        "Malts": "Pilsner, Munich".upper(),
        "Description": "Warm and malty. Like an Oktoberfest, but fruitier. Brewed as an Ale instead of a lager"
                       " because honestly, I don't have the equipment or patience to lager.".upper(),
        "Cost": nano_to_raw(.005),
        "Pour": 16,
        "BG_Color": (.8, .3, .1, .8)


    },
    2: {
        "Tap Number": 1,
        "Valve Number": 2,
        "Name": "Moving Day".upper(),
        "Style": "Barleywine".upper(),
        "IBU": 40,
        "SRM": 25,
        "ABV": 10.3,
        "FG": 1.025,
        "Hops": "Magnum".upper(),
        "Malts": "US 2-Row, Caramunich, CaraRed, Caramel 60L".upper(),
        "Description": "Sweet and strong. Simple barleywine with a slight malty finish. If you wanna know what barley"
                       " tastes like, and enjoy hangovers, have at it. Enjoy after you're done moving. Something"
                       "something stonefruit.".upper(),
        "Cost": nano_to_raw(.01),
        "Pour": 12,
        "BG_Color": (.1, .1, .7, .8)
    },
    3: {
        "Tap Number": 2,
        "Valve Number": 3,
        "Name": "Snuggle\nWith Otis".upper(),
        "Style": "Winter Warmer".upper(),
        "IBU": 25,
        "SRM": 25,
        "ABV": 5.8,
        "FG": 1.014,
        "Hops": "Cluster".upper(),
        "Malts": "US 2-Row, Crystal 90, Carapils".upper(),
        "Description": "What better way to ring in the holiday than snuggling with this pup. Cinnamon, nutmeg, and plenty of warm brown fur will keep you warm.".upper(),
        "Cost": nano_to_raw(.005),
        "Pour": 16,
        "BG_Color": (.2, 0, .4, .3)
    },
    4: {
        "Tap Number": 2,
        "Valve Number": 4,
        "Name": "End of an Era".upper(),
        "Style": "Specialty Barleywine".upper(),
        "IBU": 50,
        "SRM": 30,
        "ABV": 15.0,
        "FG": 1.033,
        "Hops": "Magnum".upper(),
        "Malts": "US 2-Row, Crystal 10".upper(),
        "Description": "Sweet, thick, alcoholic. What better way to celebrate the end than by forgetting it. ".upper(),
        "Cost": nano_to_raw(.012),
        "Pour": 8,
        "BG_Color": (0, 0, 0, .9)
    },

}

# do we want to accept payment?
payment = False

# config for hte kivy app. If it's not on the raspberry pi, don't activate GPIO, and use a timer to simulate the
# flowmeter


# when the flow meter is being monitored, it is looking for a chance from True to False for a 'click'
flow_pin_was_on = False
tap_to_flowmeter_gpio = {
    1: 4,
    2: 17
}
valve_number_to_gpio = {
    1: 18,
    2: 23,
    3: 24,
    4: 25
}
try:
    import RPi.GPIO as GPIO
    import time
    GPIO.setmode(GPIO.BCM)
    for key in tap_to_flowmeter_gpio:
        GPIO.setup(tap_to_flowmeter_gpio[key], GPIO.IN)


    for key in valve_number_to_gpio:
        GPIO.setup(valve_number_to_gpio[key], GPIO.OUT)
        GPIO.output(valve_number_to_gpio[key], False)
    raspberry_pi = True
except:
    raspberry_pi = False

Config.set('kivy', 'escape_to_exist', 1)
Config.set('graphics', 'width',  800)
Config.set('graphics', 'height', 480)

flow_meter = 0
callback_test_time = .1

t0 = 0
times = []
flow_meter_channel = 4


class LoginScreen(FloatLayout):
    def __init__(self, **kwargs):
        #self.cols = 1
        super(LoginScreen, self).__init__(**kwargs)
        splash = Image(source='images/splash.png', pos_hint={'x': 0, 'y': 0}, size_hint=(1, 1))
        self.add_widget(splash)

        Clock.schedule_once(self.MainMenu, 5)


    def MainMenu(self, dummy=None):
        self.clear_widgets(self.children)
        #self.size = (800, 480)
        global beer_list
        global flow_meter
        global flow_pin_was_on
        flow_pin_was_on = False
        flow_meter = 0
        self.clear_widgets(self.children)
        #splash = Image(source='images/splash.png', pos_hint={'x': 0, 'y': 0}, size_hint=(1, 1))
        #self.add_widget(splash)

        main_grid = GridLayout()
        main_grid.cols = 2

        tap_num = 1
        btn1 = Button(background_color=(51 / 255, 51 / 255, 51 / 255, 1),
                      background_normal='',
                      background_down='',
                      markup=True,
                      halign='center',
                      text="[size=50][font=fonts/BEER.TTF]" + beer_list[tap_num]['Name'] +'[/font][/size]\n' +
                            '[size=25]' + beer_list[tap_num]['Style'] + '\n' +
                           'ABV: %s%% | IBU: %s' % (beer_list[tap_num]['ABV'], beer_list[tap_num]['IBU']) +'[/size]',
                      font_name="fonts/Clicker - Regular.ttf",
                      color=(250 / 255, 175 / 255, 64 / 255),
                      )
        btn1.props = beer_list[tap_num]
        btn1.bind(on_release=self.BeerDescript)

        #splash = Image(source='images/splash.png', pos_hint={'x': 0, 'y': 0}, size_hint=(4, 4))
        #btn1.add_widget(splash)

        tap_num = 2
        btn2 = Button(background_color=(250 / 255, 175 / 255, 64 / 255, 1),
                      background_normal='',
                      background_down='',
                      markup=True,
                      halign='center',
                      text="[size=50][font=fonts/BEER.TTF]" + beer_list[tap_num]['Name'] +'[/font][/size]\n' +
                            '[size=25]' + beer_list[tap_num]['Style'] + '\n' +
                           'ABV: %s%% | IBU: %s' % (beer_list[tap_num]['ABV'], beer_list[tap_num]['IBU']) +'[/size]',
                      font_name="fonts/Clicker - Regular.ttf",
                      color=(51 / 255, 51 / 255, 51 / 255),
                      )
        btn2.props = beer_list[tap_num]
        btn2.bind(on_release=self.BeerDescript)

        tap_num = 3
        btn3 = Button(background_color=(250 / 255, 175 / 255, 64 / 255, 1),
                      background_normal='',
                      background_down='',
                      markup=True,
                      halign='center',
                      text="[size=50][font=fonts/BEER.TTF]" + beer_list[tap_num]['Name'] +'[/font][/size]\n' +
                            '[size=25]' + beer_list[tap_num]['Style'] + '\n' +
                           'ABV: %s%% | IBU: %s' % (beer_list[tap_num]['ABV'], beer_list[tap_num]['IBU']) +'[/size]',
                      font_name="fonts/Clicker - Regular.ttf",
                      color=(51 / 255, 51 / 255, 51 / 255),
                      )
        btn3.props = beer_list[tap_num]
        btn3.bind(on_release=self.BeerDescript)

        tap_num = 4
        btn4 = Button(background_color=(51 / 255, 51 / 255, 51 / 255, 1),
                      background_normal='#ffffff',
                      background_down='',
                      markup=True,
                      halign='center',
                      text="[size=50][font=fonts/BEER.TTF]" + beer_list[tap_num]['Name'] +'[/font][/size]\n' +
                            '[size=25]' + beer_list[tap_num]['Style'] + '\n' +
                           'ABV: %s%% | IBU: %s' % (beer_list[tap_num]['ABV'], beer_list[tap_num]['IBU']) +'[/size]',
                      font_name="fonts/Clicker - Regular.ttf",
                      color=(250 / 255, 175 / 255, 64 / 255, 1),
                      )
        btn4.props = beer_list[tap_num]
        btn4.bind(on_release=self.BeerDescript)

        main_grid.add_widget(btn1)
        main_grid.add_widget(btn2)
        main_grid.add_widget(btn3)
        main_grid.add_widget(btn4)
        self.add_widget(main_grid)


    def BeerDescript(self, value):
        self.cols = 2
        self.clear_widgets(self.children)
        left_float = FloatLayout()
        left_float.add_widget(
            Label(text=value.props['Name'].replace('\n', ' '),
                  font_size=40,
                  pos_hint={'x': 0, 'top': 1.4},
                  font_name="fonts/BEER.TTF",
                  color=(51 / 255, 51 / 255, 51 / 255, 1)
                  )
        )

        left_float.add_widget(
            Label(
                text="[size=35]%soz - %.0f Chips[/size]\n(%s Stones, %s Nano)\nABV: %s%%\n%s IBU\nMalts: %s\nHops: %s\n\n%s\n\nTap Number: %s"%(
                    value.props['Pour'], value.props['Cost']/(10**25), value.props['Cost']/(10**28), value.props['Cost']/(10**30),value.props['ABV'],
                    value.props['IBU'], value.props['Malts'], value.props['Hops'], value.props['Description'],
                    value.props['Tap Number']),
                markup=True,
                text_size=(left_float.width*3.5, None),
                pos_hint={'x': -.25, 'top': .95},
                  font_name="fonts/Clicker - Regular.ttf",
                  color=(51 / 255, 51 / 255, 51 / 255, 1)
                ))
        #right_float = FloatLayout()

        beer_img = Image(
            source='images/download.jpg',
            size=(.5, .5),
            pos_hint={'x': .2, 'top': 1.2}
        )

        btn2 = Button(text='PURCHASE',
                      font_size=45,
                      size_hint=(.4, .2),
                      pos_hint={'x': .5, 'top': .5},
                      background_color=(51 / 255, 51 / 255, 51 / 255, 1),
                      color=(250 / 255, 175 / 255, 64 / 255, 1),
                      font_name="fonts/Clicker - Regular.ttf",
                      )
        btn2.props = value.props
        btn2.bind(on_release=partial(self.QRScreen))
        left_float.add_widget(btn2)

        btn1 = Button(text='MENU',
                      font_size=45,
                      size_hint=(.4, .2),
                      pos_hint={'x': .5, 'top': .25},
                      background_color=(51 / 255, 51 / 255, 51 / 255, 1),
                      color=(250 / 255, 175 / 255, 64 / 255, 1),
                      font_name="fonts/Clicker - Regular.ttf",
                      )
        btn1.bind(on_release=self.MainMenu)
        left_float.add_widget(btn1)
        left_float.add_widget(beer_img)

        self.add_widget(left_float)
        #self.add_widget(right_float)


    def QRScreen(self, value):
        global payment
        self.clear_widgets(self.children)
        splash = Image(source='images/splash.png', pos_hint={'x': 0, 'y': 0}, size_hint=(1, 1))
        self.add_widget(splash)
        #self.cols = 1

        props = value.props
        if payment:
            address = generate_account()
        else:
            address = {"account": "test", "private": "test"}

        props['account'] = address['account']
        props['key'] = address['private']

        with open("transaction_history.txt", "a") as myfile:
            myfile.write("%s\n%s\n" % (props['account'], props['key']))
        try:
            qrcode = generate_qr(props['account'], props['Cost'], fill_color=(51, 51, 51), back_color=(250, 175, 64))
        except:
            qrcode = generate_qr(props['account'], props['Cost'])
        data = BytesIO()

        qrcode.save(data, format='png')
        data.seek(0)
        img = CoreImage(data, ext="png")


        #self.add_widget(Button(text='You have 30 seconds to purchase %s'%value.text[9:], id='btn1'))

        #crudeclock = IncrediblyCrudeClock(pos_hint={'x': 0, 'y': -.4})
        amount = Label(text="[font=fonts/BEER.TTF][size=40]%s[/size][/font]\n%s oz\n%.0f Chips\n(%s Stones, %s Nano)\nTap %s"%(props['Name'].replace('\n', ' '), props['Pour'], props['Cost']/10**25, props['Cost']/10**28,props['Cost']/10**30, props['Tap Number']),
                       pos_hint={'x':0, 'y':.31},
                       markup=True,
                       font_size=25,
                       font_name='fonts/Clicker - Regular.ttf',
                       halign="center",
                       color=(51 / 255, 51 / 255, 51 / 255, 1))

        qr_code = Image(texture=img.texture, pos_hint={'x': .25, 'y': .13}, size_hint=(.5, .5))

        #layout_layer.add_widget(crudeclock)
        layout_layer = FloatLayout()
        layout_layer.add_widget(qr_code)
        layout_layer.add_widget(amount)
        self.add_widget(layout_layer)
        #crudeclock.start()
        #event = Clock.schedule_once(self.MainMenu, 120)
        #event2 = Clock.schedule_interval(partial(self.InternalCheck, event, props), 1/2)
        if payment:
            event = Clock.schedule_interval(partial(self.CheckPayment, props), 1 / 3)
        else:
            Clock.schedule_once(partial(self.PaymentReceived, props), 3)

    def CheckPayment(self, props, something):
        global payment
        if payment:
            checkbalance = check_balance(props['account'], props['Cost'])
        #else:
        #    checkbalance = True
        if checkbalance:
            #event.cancel()
            self.PaymentReceived(props, None)
            return False
        else:
            return True

    def PaymentReceived(self, props, dummy):
        self.clear_widgets(self.children)
        #print(props)
        self.add_widget(
            Label(
                text="[size=60][font=fonts/Clicker - Regular.ttf]PAYMENT RECEIVED![/font][/size]",
                markup=True,
                valign='center',
                halign='center',
                color=(51 / 255, 51 / 255, 51 / 255, 1),

                )
        )
        event = Clock.schedule_once(partial(self.Dispensing, props), 1)

    def Dispensing(self, props, value):
        self.clear_widgets(self.children)
        global flow_meter
        global t0
        # turn our GPIO on!
        if raspberry_pi:
            GPIO.output(valve_number_to_gpio[props["Valve Number"]], True)
        t0=0
        flow_meter = 0
        img = Image(source='images/download.jpg')
        title = Label(markup=True,
                      font_size=55,
                      halign='center',
                      pos_hint ={'top':1.35},
                      color=(51 / 255, 51 / 255, 51 / 255, 1),
                      font_name='fonts/Clicker - Regular.ttf',
                      text='[font=fonts/BEER.TTF]%s[/font]\nTAP NUMBER %s'%(props['Name'], props['Tap Number']),
                      )

        label = Label(markup=True,
                      font_size=55,
                      halign='center',
                      pos_hint={'top':.65},
                      color=(51 / 255, 51 / 255, 51 / 255, 1),
                      font_name='fonts/Clicker - Regular.ttf',
                      )
        self.add_widget(img)
        self.add_widget(title)
        self.add_widget(label)

        event = Clock.schedule_interval(
            partial(self.update_label, label, img, props['Pour']),
            1/5)


        event2 = Clock.schedule_interval(partial(self.CheckFlowMeter, event, props, props['Pour']), 1/75)
        #event = Clock.schedule_once(self.ThankYou, 10)

    def ThankYou(self, value):
        global times
        #print('FPS', times[:30])
        self.clear_widgets(self.children)
        self.add_widget(
            Label(
                text="[size=100][font=fonts/Clicker - Regular.ttf]ENJOY![/font][/size]",
                markup=True,
                valign='center',
                halign='center',
                color=(51 / 255, 51 / 255, 51 / 255, 1),
            )
        )
        #event = Clock.schedule_once(partial(self.MainMenu), 2)
        event = Clock.schedule_once(self.MainMenu, 2)

    def CheckFlowMeter(self, event, props, pour, something):
        global flow_meter
        global t0
        global times
        global flow_pin_was_on
        new_time = time.time()
        times.append(1/(t0-new_time))
        t0 = new_time
        if raspberry_pi:
            flow_pin_currently_on = GPIO.input(tap_to_flowmeter_gpio[props["Tap Number"]])
            if flow_pin_currently_on and not flow_pin_was_on:
                flow_meter += 0.075142222
            flow_pin_was_on = flow_pin_currently_on
        else:
            flow_meter += 1 / 20

        if flow_meter >= int(pour):
            event.cancel()
            if raspberry_pi:
                GPIO.output(valve_number_to_gpio[props["Valve Number"]], False)
            self.ThankYou(None)
            return False


    def update_label(self, label, img, pour, something):
        label.text = "[size=60]%.1f OF %s OZ\nDISPENSED[/size]"%(flow_meter, pour)
        if (flow_meter/pour) < .15:
            img.source = 'images/beer0.png'
        if .15 <= (flow_meter/pour) < .3:
            img.source = 'images/beer15.png'
        if .3 <= (flow_meter/pour) < .45:
            img.source = 'images/beer30.png'
        if .45 <= (flow_meter/pour) < .6:
            img.source = 'images/beer45.png'
        if .6 <= (flow_meter/pour) < .75:
            img.source = 'images/beer60.png'
        if .75 <= (flow_meter/pour) < 90:
            img.source = 'images/beer75.png'
        if .9 <= (flow_meter/pour):
            img.source = 'images/beer90.png'


class SimpleKivy(App):
    def build(self):
        return LoginScreen(size=(800, 480))


if __name__=='__main__':
    SimpleKivy().run()
