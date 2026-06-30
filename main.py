import json
import os
import threading
import queue
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from pywebostv.connection import WebOSClient
from pywebostv.controls import MediaControl, SystemControl

# ======================================
# CONFIGURAÇÕES
# ======================================

IP_DA_TV = "192.168.100.2"
ARQUIVO_CHAVE = "tv_token.json"


# ======================================
# CLASSE SMART TV
# ======================================

class SmartTV:

    def __init__(self, ip):

        self.ip = ip

        self.client = None
        self.media = None
        self.system = None

        self.volume = "--"

        self.status = "Conectando..."

        self.fila = queue.Queue()

        threading.Thread(target=self.conectar,
                         daemon=True).start()

        threading.Thread(target=self.processar_fila,
                         daemon=True).start()

        threading.Thread(target=self.monitorar_volume,
                         daemon=True).start()

    def conectar(self):

        try:

            self.client = WebOSClient(self.ip,
                                      secure=True)

            self.client.connect()

            store = {}

            if os.path.exists(ARQUIVO_CHAVE):

                with open(ARQUIVO_CHAVE, "r") as f:
                    store = json.load(f)

            for status in self.client.register(store):
                pass

            with open(ARQUIVO_CHAVE, "w") as f:
                json.dump(store, f)

            self.media = MediaControl(self.client)
            self.system = SystemControl(self.client)

            self.status = "🟢 Conectada"

        except Exception as e:

            print(e)

            self.status = "🔴 Erro"

    def monitorar_volume(self):

        while True:

            if self.media:

                try:

                    dados = self.media.get_volume()

                    if isinstance(dados, dict):

                        if "volume" in dados:
                            self.volume = str(dados["volume"])

                except:
                    pass

            time.sleep(1)

    def processar_fila(self):

        while True:

            cmd = self.fila.get()

            if self.media:

                try:

                    if cmd == "up":
                        self.media.volume_up()

                    elif cmd == "down":
                        self.media.volume_down()

                except Exception as e:

                    print(e)

            self.fila.task_done()

    def enviar(self, comando):

        self.fila.put(comando)


# ======================================
# INTERFACE
# ======================================

class TelaPrincipal(BoxLayout):

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.orientation = "vertical"

        self.padding = dp(20)

        self.spacing = dp(20)

        self.tv = SmartTV(IP_DA_TV)

        self.lblTitulo = Label(
            text="Controle LG",
            font_size="28sp",
            size_hint=(1, .15)
        )

        self.add_widget(self.lblTitulo)

        self.lblStatus = Label(
            text="Conectando...",
            font_size="20sp",
            size_hint=(1, .10)
        )

        self.add_widget(self.lblStatus)

        self.lblVolume = Label(
            text="--",
            font_size="70sp",
            size_hint=(1, .35)
        )

        self.add_widget(self.lblVolume)

        linha = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint=(1, .40)
        )

        self.btnMais = Button(
            text="VOL +",
            font_size="28sp"
        )

        self.btnMenos = Button(
            text="VOL -",
            font_size="28sp"
        )

        self.btnMais.bind(on_release=self.volume_mais)
        self.btnMenos.bind(on_release=self.volume_menos)

        linha.add_widget(self.btnMais)
        linha.add_widget(self.btnMenos)

        self.add_widget(linha)

        Clock.schedule_interval(self.atualizar, 0.5)

    def volume_mais(self, botao):

        self.tv.enviar("up")

    def volume_menos(self, botao):

        self.tv.enviar("down")

    def atualizar(self, dt):

        self.lblStatus.text = self.tv.status

        self.lblVolume.text = self.tv.volume


# ======================================
# APP
# ======================================

class ControleLG(App):

    def build(self):

        return TelaPrincipal()


if __name__ == "__main__":

    ControleLG().run()
