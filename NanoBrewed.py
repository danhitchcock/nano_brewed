import time
from kivy.app import App
from kivy.uix.label import Label
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from functools import partial
from io import BytesIO
from kivy.config import Config
from rpc_bindings import open_account, generate_account, generate_qr, nano_to_raw, receive_all, send_all, check_balance

# this file will contain your account name. I left it intentionally missing from the repo
with open('my_account.txt') as f:
    for line in f:
        my_account = line

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

# the beers. has beer information and keg information
# the tap number will determine which flow_meter to use
# the valve number controls whichever valve
beer_list = {
    1: {
        "Tap Number": 1,
        "Valve Number": 1,
        "Name": "Dantoberfest",
        "Style": "Mocktoberfest Ale",
        "IBU": 22,
        "SRM": 9,
        "ABV": 8.5,
        "FG": 1.012,
        "Hops": "Hallertauer",
        "Malts": "Pilsner, Munich",
        "Description": "Warm and malty. Like an Oktoberfest, but fruitier. Brewed as an Ale instead of a lager"
                       " because honestly, I don't have the equipment or patience to lager.",
        "Cost": nano_to_raw(.01),
        "Pour": 16,
        "BG_Color": (.8, .3, .1, .8)


    },
    2: {
        "Tap Number": 1,
        "Valve Number": 2,
        "Name": "Moving Day",
        "Style": "Barleywine",
        "IBU": 40,
        "SRM": 25,
        "ABV": 10.3,
        "FG": 1.025,
        "Hops": "Magnum",
        "Malts": "US 2-Row, Caramunich, CaraRed, Caramel 60L",
        "Description": "Sweet and strong. Simple barleywine with a slight malty finish. If you wanna know what barley"
                       " tastes like, and enjoy hangovers, have at it. Enjoy after you're done moving. Something"
                       "something stonefruit.",
        "Cost": nano_to_raw(.01),
        "Pour": 12,
        "BG_Color": (.1, .1, .7, .8)
    },
    3: {
        "Tap Number": 2,
        "Valve Number": 3,
        "Name": "Snuggle\nWith Otis",
        "Style": "Winter Warmer",
        "IBU": 25,
        "SRM": 25,
        "ABV": 5.8,
        "FG": 1.014,
        "Hops": "Cluster",
        "Malts": "US 2-Row, Crystal 90, Carapils",
        "Description": "What better way to ring in the holiday than snuggling with this pup. Cinnamon, nutmeg, and plenty of warm brown fur will keep you warm.",
        "Cost": nano_to_raw(.01),
        "Pour": 16,
        "BG_Color": (.2, 0, .4, .3)
    },
    4: {
        "Tap Number": 2,
        "Valve Number": 4,
        "Name": "End of an Era",
        "Style": "Specialty Barleywine",
        "IBU": 50,
        "SRM": 30,
        "ABV": 15.0,
        "FG": 1.033,
        "Hops": "Magnum",
        "Malts": "US 2-Row, Crystal 10",
        "Description": "Sweet, thick, alcoholic. What better way to celebrate the end than by forgetting it. ",
        "Cost": nano_to_raw(.01),
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
        splash = Image(source='images/splash.png', pos_hint={'x': 0, 'y': 0}, size_hint=(1, 1))
        self.add_widget(splash)

        main_grid = GridLayout()
        main_grid.cols = 2

        tap_num = 1
        btn1 = Button(markup=True,
                      halign='center',
                      background_color=(1, 1, 1, 0),
                      #background_normal='/images/splash.png',
                      #background_down='/images/splash.png',
                      text="[size=60]" + beer_list[tap_num]['Name'] +'[/size]\n' +
                            '[size=25]' + beer_list[tap_num]['Style'] + '\n' +
                           'ABV: %s%% | IBU: %s' % (beer_list[tap_num]['ABV'], beer_list[tap_num]['IBU']) +'[/size]'
                      )
        btn1.props = beer_list[tap_num]
        btn1.bind(on_release=self.BeerDescript)

        #splash = Image(source='images/splash.png', pos_hint={'x': 0, 'y': 0}, size_hint=(4, 4))
        #btn1.add_widget(splash)

        tap_num = 2
        btn2 = Button(background_normal='',
                      markup=True,
                      halign='center',
                      background_color=(1, 1, 1, 0),
                      text="[size=60]" + beer_list[tap_num]['Name'] +'[/size]\n' +
                            '[size=25]' + beer_list[tap_num]['Style'] + '\n' +
                           'ABV: %s%% | IBU: %s' % (beer_list[tap_num]['ABV'], beer_list[tap_num]['IBU']) +'[/size]'
                      )
        btn2.props = beer_list[tap_num]
        btn2.bind(on_release=self.BeerDescript)

        tap_num = 3
        btn3 = Button(background_normal='',
                      markup=True,
                      halign='center',
                      background_color=(1, 1, 1, 0),
                      text="[size=60]" + beer_list[tap_num]['Name'] +'[/size]\n' +
                            '[size=25]' + beer_list[tap_num]['Style'] + '\n' +
                           'ABV: %s%% | IBU: %s' % (beer_list[tap_num]['ABV'], beer_list[tap_num]['IBU']) +'[/size]'
                      )
        btn3.props = beer_list[tap_num]
        btn3.bind(on_release=self.BeerDescript)

        tap_num = 4
        btn4 = Button(background_normal='',
                      markup=True,
                      halign='center',
                      background_color=(1, 1, 1, 0),
                      text="[size=60]" + beer_list[tap_num]['Name'] +'[/size]\n' +
                            '[size=25]' + beer_list[tap_num]['Style'] + '\n' +
                           'ABV: %s%% | IBU: %s' % (beer_list[tap_num]['ABV'], beer_list[tap_num]['IBU']) +'[/size]'
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
        #print(value.props['BG_Color'])

        #left_float.canvas.add(Color(rgba=value.props['BG_Color']))
        #left_float.canvas.add(Rectangle(pos=(0, 0), size=(400, 480), ))
        left_float.add_widget(Label(text=value.props['Name'], font_size=40, pos_hint={'x': 0, 'top': 1.4}))
        left_float.add_widget(
            Label(
                text="%soz -- %s Nano\nABV: %s%%\n%s IBU\nMalts: %s\nHops: %s\n\n%s\n\nTap Number: %s"%(
                    value.props['Pour'], value.props['Cost']/(10**30), value.props['ABV'],
                    value.props['IBU'], value.props['Malts'], value.props['Hops'], value.props['Description'],
                    value.props['Tap Number']),
                text_size=(left_float.width*2, None),
                pos_hint={'x': -.3, 'top': .95}
                ))
        #right_float = FloatLayout()

        btn2 = Button(text='Purchase %s' % (value.props['Name']), font_size=25, size_hint=(.4, .2),
                      pos_hint={'x': .5, 'top' : .8}, background_color=(0, 1, 0, .8))
        btn2.props = value.props
        btn2.bind(on_release=partial(self.BuyBeer))
        left_float.add_widget(btn2)

        btn1 = Button(text='Back to Main Menu', font_size=25, size_hint=(.4, .2), pos_hint={'x': .5, 'top': .4},
                      background_color=(1, 0, 0, .8))
        btn1.bind(on_release=self.MainMenu)
        left_float.add_widget(btn1)

        self.add_widget(left_float)
        #self.add_widget(right_float)

    def BuyBeer(self, value):
        global payment

        self.cols = 1
        self.clear_widgets(self.children)
        props = value.props
        if payment:
            address = generate_account()
        else:
            address = {"account":"test", "private":"test"}

        props['account'] = address['account']
        props['key'] = address['private']

        with open("transaction_history.txt", "a") as myfile:
            myfile.write("%s\n%s\n" % (props['account'], props['key']))

        qrcode = generate_qr(props['account'], props['Cost'])
        data = BytesIO()

        qrcode.save(data, format='png')
        data.seek(0)
        img = CoreImage(data, ext="png")


        #self.add_widget(Button(text='You have 30 seconds to purchase %s'%value.text[9:], id='btn1'))

        #crudeclock = IncrediblyCrudeClock(pos_hint={'x': 0, 'y': -.4})
        amount = Label(text="%s\n%s oz\n%s Nano\nTap %s"%(props['Name'], props['Pour'], props['Cost']/10**30, props['Tap Number']),
                       pos_hint={'x':0, 'y':.37},
                       font_size=25, halign="center")

        qr_code = Image(texture=img.texture, pos_hint={'x': .25, 'y': .2}, size_hint=(.5, .5))

        #layout_layer.add_widget(crudeclock)
        layout_layer = FloatLayout()
        layout_layer.add_widget(qr_code)
        layout_layer.add_widget(amount)
        self.add_widget(layout_layer)
        #crudeclock.start()
        #event = Clock.schedule_once(self.MainMenu, 120)
        #event2 = Clock.schedule_interval(partial(self.InternalCheck, event, props), 1/2)
        if payment:
            event = Clock.schedule_interval(partial(self.InternalCheck, props), 1 / 3)
        else:
            Clock.schedule_once(partial(self.PaymentReceived, props), 3)

    def InternalCheck(self, props, something):
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
        self.add_widget(Label(text="[size=60]Payment Received![/size]", markup=True, valign='center', halign='center'))
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
        label = Label(markup=True, halign='center', valign='center')
        self.add_widget(label)

        event = Clock.schedule_interval(
            partial(self.update_label, label, props['Pour']),
            1/5)
        event2 = Clock.schedule_interval(partial(self.CheckFlowMeter, event, props, props['Pour']), 1/75)
        #event = Clock.schedule_once(self.ThankYou, 10)

    def ThankYou(self, value):
        global times
        #print('FPS', times[:30])
        self.clear_widgets(self.children)
        self.add_widget(Label(text="[size=60]Thank you![/size]", markup=True, valign='center', halign='center'))
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


    def update_label(self, label, pour, something):
        global flow_meter
        label.text="[size=60]%.1f of %s oz\ndispensed[/size]"%(flow_meter, pour)


class SimpleKivy(App):
    def build(self):
        return LoginScreen(size=(800, 480))


if __name__=='__main__':
    SimpleKivy().run()
