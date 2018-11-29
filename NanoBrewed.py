import os
import time
from kivy.app import App
from math import ceil, floor
from kivy.uix.label import Label
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.animation import Animation
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.textinput import TextInput
from kivy.graphics import Rectangle, Color
from kivy.uix.button import Button
from kivy.clock import Clock
from functools import partial
from io import BytesIO
import json
import pycurl
import json
from io import BytesIO
import qrcode
from kivy.config import Config


def perform_curl(data=None, URL=None):
    if URL is None:
        URL = '192.168.3.103:7076'

    c = pycurl.Curl()
    c.setopt(c.URL, URL)
    buf = BytesIO()
    if data:
        data = json.dumps(data)
        c.setopt(pycurl.POSTFIELDS, data)

    c.setopt(c.WRITEFUNCTION, buf.write)
    c.perform()
    results = buf.getvalue()
    results = results.decode("utf-8")
    results = json.loads(results)
    buf.close()
    return results


def send_block(origin, key, amount, destination, rep=None):
    balance = check_balance(origin)[0]
    balance = int(balance - amount)
    previous = get_previous_hash(origin)
    print(balance)
    if rep is None:
        rep = "xrb_1brainb3zz81wmhxndsbrjb94hx3fhr1fyydmg6iresyk76f3k7y7jiazoji"
    data = {
        "action": "block_create",
        "type": "state",
        "previous": previous,
        "account": origin,
        "balance": balance,
        "link": destination,
        "representative": rep,
        "key": key
    }
    results = perform_curl(data)
    return results


def open_block(account, key, rep=None):
    """

    :param account: str account to open
    :param key: str account private key
    :param rep: str representative
    :return: str block-string for json
    """
    if rep is None:
        rep = "xrb_1brainb3zz81wmhxndsbrjb94hx3fhr1fyydmg6iresyk76f3k7y7jiazoji"
    sent_hash = get_pending(account)["blocks"][0]
    sent_block = get_block_by_hash(sent_hash)
    sent_previous_hash = sent_block['previous']
    sent_previous_block = get_block_by_hash(sent_previous_hash)
    amount = (int(sent_previous_block['balance']) - int(sent_block['balance']))
    data = {
        'action': 'block_create',
        'type': 'state',
        'previous': '0',
        'account': account,
        'representative': rep,
        'balance': amount,
        'link': sent_hash,
        'key': key,
    }
    results = perform_curl(data)
    return results


def receive_block(account, key, sent_hash, rep=None):
    """
    :param account: str account to open
    :param key: str account private key
    :param rep: str representative
    :return: str block-string for json
    """
    if rep is None:
        rep = "xrb_1brainb3zz81wmhxndsbrjb94hx3fhr1fyydmg6iresyk76f3k7y7jiazoji"
    previous = get_previous_hash(account)
    sent_block = get_block_by_hash(sent_hash)
    sent_previous_hash = sent_block['previous']
    sent_previous_block = get_block_by_hash(sent_previous_hash)
    amount = (int(sent_previous_block['balance']) - int(sent_block['balance']))
    amount = check_balance(account)[0] + amount
    print(amount)
    data = {
        'action': 'block_create',
        'type': 'state',
        'previous': previous,
        'account': account,
        'representative': rep,
        'balance': amount,
        'link': sent_hash,
        'key': key,
    }
    results = perform_curl(data)
    return results


def send(*argv):
    """
    origin, key, amount, destination, rep=None
    """
    results = process_block(send_block(*argv))
    return results


def open(*argv):
    """
    account, key, rep=None
    """
    results = process_block(open_block(*argv))
    return results


def receive_all(account, key, rep=None):
    hashes = []
    sent_hashes = get_pending(account)["blocks"]
    if len(sent_hashes) < 1:
        return "No Pending Transactions."
    else:
        for sent_hash in sent_hashes:
            results = process_block(receive_block(account, key, sent_hash, rep))
            hashes.append(results)
    return hashes


def check_balance(account, amount=None, URL=None):
    data = {
        "action": "account_balance",
        "account": account
    }
    results = perform_curl(data, URL)
    if amount is None:
        return [int(results['balance']), int(results['pending'])]
    else:
        return int(results['pending']) == amount


def generate_account():
    data = {"action": "key_create"}
    return (perform_curl(data))


def get_previous_hash(account):
    data = {
        "action": "account_history",
        "account": account,
        "count": "1"
    }
    results = perform_curl(data)
    return results['history'][0]['hash']


def get_block_by_hash(hash):
    data = {
        "action": "block",
        "hash": hash
    }
    results = perform_curl(data)
    return json.loads(results['contents'])


def get_pending(account):
    data = {
        "action": "pending",
        "account": account,
        "count": "-1"
    }
    return perform_curl(data)


def generate_qr(account, amount=0):
    account_amount = 'xrb:%s?amount=%s' % (account, amount)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(account_amount)
    img = qr.make_image(fill_color='black', back_color='white')
    return img


def process_block(block):
    data = {"action": "process"}
    data["block"] = block['block']
    return perform_curl(data)


def nano_to_raw(amount):
    return round(int(amount*10**30), -20)


def raw_to_nano(amount):
    return amount/10**30


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

flow_meter_channel = 4
flow_pin_was_on = False
try:
    import RPi.GPIO as GPIO
    import time
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(flow_meter_channel, GPIO.IN)
    raspberry_pi = True
except:
    raspberry_pi = False

Config.set('kivy', 'escape_to_exist', 1)
Config.set('graphics', 'width',  800)
Config.set('graphics', 'height', 480)

flow_meter = 0
callback_test_time = .1
payment = False
t0 = 0
times=[]


class LoginScreen(GridLayout):
    def __init__(self, **kwargs):
        #self.size = (800, 480)
        global beer_list
        global flow_meter
        flow_meter = 0
        super(LoginScreen, self).__init__(**kwargs)
        self.clear_widgets(self.children)
        self.cols = 2

        tap_num = 1
        btn1 = Button(background_normal='', markup=True, halign='center', background_color=beer_list[tap_num]['BG_Color'],
                      text="[size=60]" + beer_list[tap_num]['Name'] +'[/size]\n' +
                            '[size=25]' + beer_list[tap_num]['Style'] + '\n' +
                           'ABV: %s%% | IBU: %s' % (beer_list[tap_num]['ABV'], beer_list[tap_num]['IBU']) +'[/size]'
                      )
        btn1.props = beer_list[tap_num]
        btn1.bind(on_release=self.BeerDescript)

        tap_num = 2
        btn2 = Button(background_normal='', markup=True, halign='center', background_color=beer_list[tap_num]['BG_Color'],
                      text="[size=60]" + beer_list[tap_num]['Name'] +'[/size]\n' +
                            '[size=25]' + beer_list[tap_num]['Style'] + '\n' +
                           'ABV: %s%% | IBU: %s' % (beer_list[tap_num]['ABV'], beer_list[tap_num]['IBU']) +'[/size]'
                      )
        btn2.props = beer_list[tap_num]
        btn2.bind(on_release=self.BeerDescript)

        tap_num = 3
        btn3 = Button(background_normal='', markup=True, halign='center', background_color=beer_list[tap_num]['BG_Color'],
                      text="[size=60]" + beer_list[tap_num]['Name'] +'[/size]\n' +
                            '[size=25]' + beer_list[tap_num]['Style'] + '\n' +
                           'ABV: %s%% | IBU: %s' % (beer_list[tap_num]['ABV'], beer_list[tap_num]['IBU']) +'[/size]'
                      )
        btn3.props = beer_list[tap_num]
        btn3.bind(on_release=self.BeerDescript)

        tap_num = 4
        btn4 = Button(background_normal='', markup=True, halign='center', background_color=beer_list[tap_num]['BG_Color'],
                      text="[size=60]" + beer_list[tap_num]['Name'] +'[/size]\n' +
                            '[size=25]' + beer_list[tap_num]['Style'] + '\n' +
                           'ABV: %s%% | IBU: %s' % (beer_list[tap_num]['ABV'], beer_list[tap_num]['IBU']) +'[/size]'
                      )
        btn4.props = beer_list[tap_num]
        btn4.bind(on_release=self.BeerDescript)

        self.add_widget(btn1)
        self.add_widget(btn2)
        self.add_widget(btn3)
        self.add_widget(btn4)

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

    def MainMenu(self, value):
        self.__init__()

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
        layout_layer = FloatLayout()
        #crudeclock = IncrediblyCrudeClock(pos_hint={'x': 0, 'y': -.4})
        amount = Label(text="%s\n%s oz\n%s Nano\nTap %s"%(props['Name'], props['Pour'], props['Cost']/10**30, props['Tap Number']),
                       pos_hint={'x':0, 'y':.37},
                       font_size=25, halign="center")

        qr_code = Image(texture=img.texture, pos_hint={'x': .25, 'y': .2}, size_hint=(.5, .5))

        #layout_layer.add_widget(crudeclock)
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
        print(times[:30])
        self.clear_widgets(self.children)
        self.add_widget(Label(text="[size=60]Thank you![/size]", markup=True, valign='center', halign='center'))
        event = Clock.schedule_once(self.MainMenu, 2)

    def CheckFlowMeter(self, event, props, pour, something):
        global flow_meter
        global t0
        global times
        global flow_pin_was_on
        global flow_meter_channel
        new_time = time.time()
        times.append(1/(t0-new_time))
        t0 = new_time
        if raspberry_pi:
            flow_pin_currently_on = GPIO.input(flow_meter_channel)
            if flow_pin_currently_on and not flow_pin_was_on:
                flow_meter += 0.075142222
            flow_pin_was_on = flow_pin_currently_on
        else:
            flow_meter += 1 / 20



        if flow_meter >= int(pour):
            event.cancel()
            self.ThankYou(None)
            return False


    def update_label(self, label, pour, something):
        global flow_meter
        label.text="[size=60]%.1f of %s oz\ndispensed[/size]"%(flow_meter, pour)


class IncrediblyCrudeClock(Label):
    a = NumericProperty(60)  # seconds

    def start(self):
        Animation.cancel_all(self)  # stop any current animations
        self.anim = Animation(a=0, duration=self.a)
        def finish_callback(animation, incr_crude_clock):
            incr_crude_clock.text = "FINISHED"
        self.anim.bind(on_complete=finish_callback)
        self.anim.start(self)

    def on_a(self, instance, value):
        self.text = 'Please make a payment.\n  You have ' + str(floor(value)) + ' seconds.'


class SimpleKivy(App):
    def build(self):
        return LoginScreen(size=(800, 480))


if __name__=='__main__':
    SimpleKivy().run()
