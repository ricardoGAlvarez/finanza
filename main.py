import sqlite3
from datetime import datetime

from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import (
    IconLeftWidget,
    MDList,
    TwoLineAvatarListItem,
)
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField


class FinanceDB:
    def __init__(self, db_name="finanzas.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.crear_tablas()

    def crear_tablas(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                categoria TEXT NOT NULL,
                monto REAL NOT NULL,
                fecha TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def insertar_movimiento(self, tipo, categoria, monto, fecha):
        self.cursor.execute(
            """
            INSERT INTO movimientos (tipo, categoria, monto, fecha)
            VALUES (?, ?, ?, ?)
            """,
            (tipo, categoria, monto, fecha),
        )
        self.conn.commit()

    def obtener_movimientos(self):
        self.cursor.execute(
            "SELECT tipo, categoria, monto, fecha FROM movimientos ORDER BY id DESC"
        )
        return self.cursor.fetchall()

    def obtener_balance(self):
        self.cursor.execute(
            "SELECT tipo, SUM(monto) FROM movimientos GROUP BY tipo"
        )
        datos = dict(self.cursor.fetchall())
        ingresos = datos.get("Ingreso", 0.0)
        gastos = datos.get("Gasto", 0.0)
        return ingresos, gastos, (ingresos - gastos)


class FinanceApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"
        self.db = FinanceDB()

        screen = MDScreen()
        root_layout = MDBoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(12),
        )

        # Tarjeta de Balance
        self.card_balance = MDCard(
            orientation="vertical",
            padding=dp(16),
            size_hint=(1, None),
            height=dp(100),
            elevation=2,
            radius=[dp(12)],
        )
        self.lbl_balance = MDLabel(
            text="Balance: $0.00",
            halign="center",
            font_style="H5",
            theme_text_color="Primary",
        )
        self.lbl_resumen = MDLabel(
            text="Ingresos: $0.00 | Gastos: $0.00",
            halign="center",
            font_style="Caption",
            theme_text_color="Secondary",
        )
        self.card_balance.add_widget(self.lbl_balance)
        self.card_balance.add_widget(self.lbl_resumen)
        root_layout.add_widget(self.card_balance)

        # Campos de entrada
        self.txt_monto = MDTextField(
            hint_text="Monto",
            input_filter="float",
            size_hint_x=1,
        )
        root_layout.add_widget(self.txt_monto)

        # Selectores (Tipo y Categoría)
        selectors_layout = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(48),
        )

        self.btn_tipo = MDRaisedButton(
            text="Tipo",
            size_hint_x=0.5,
            on_release=self.abrir_menu_tipo,
        )
        self.btn_categoria = MDRaisedButton(
            text="Categoría",
            size_hint_x=0.5,
            on_release=self.abrir_menu_categoria,
        )
        selectors_layout.add_widget(self.btn_tipo)
        selectors_layout.add_widget(self.btn_categoria)
        root_layout.add_widget(selectors_layout)

        # Botón Guardar
        btn_guardar = MDRaisedButton(
            text="Registrar Movimiento",
            size_hint_x=1,
            md_bg_color=self.theme_cls.primary_color,
            on_release=self.guardar_registro,
        )
        root_layout.add_widget(btn_guardar)

        # Historial de transacciones
        lbl_historial = MDLabel(
            text="Últimos Movimientos",
            font_style="Subtitle2",
            size_hint_y=None,
            height=dp(24),
        )
        root_layout.add_widget(lbl_historial)

        scroll = ScrollView()
        self.lista_movimientos = MDList()
        scroll.add_widget(self.lista_movimientos)
        root_layout.add_widget(scroll)

        screen.add_widget(root_layout)

        # Menús desplegables
        self.tipo_seleccionado = None
        self.categoria_seleccionada = None
        self.configurar_menus()
        self.actualizar_ui()

        return screen

    def configurar_menus(self):
        tipos = ["Ingreso", "Gasto"]
        items_tipo = [
            {
                "viewclass": "OneLineListItem",
                "text": t,
                "on_release": lambda x=t: self.seleccionar_tipo(x),
            }
            for t in tipos
        ]
        self.menu_tipo = MDDropdownMenu(
            caller=self.btn_tipo,
            items=items_tipo,
            width_mult=3,
        )

        self.categorias_por_tipo = {
            "Ingreso": ["Sueldo", "Ventas", "Inversiones", "Otros"],
            "Gasto": [
                "Comida",
                "Transporte",
                "Servicios",
                "Salud",
                "Educación",
                "Ocio",
            ],
        }

    def abrir_menu_tipo(self, instance):
        self.menu_tipo.open()

    def seleccionar_tipo(self, valor):
        self.tipo_seleccionado = valor
        self.btn_tipo.text = valor
        self.menu_tipo.dismiss()

        # Actualizar opciones de categoría según el tipo
        cats = self.categorias_por_tipo.get(valor, ["General"])
        items_cat = [
            {
                "viewclass": "OneLineListItem",
                "text": c,
                "on_release": lambda x=c: self.seleccionar_categoria(x),
            }
            for c in cats
        ]
        self.menu_cat = MDDropdownMenu(
            caller=self.btn_categoria,
            items=items_cat,
            width_mult=4,
        )
        self.btn_categoria.text = "Categoría"
        self.categoria_seleccionada = None

    def abrir_menu_categoria(self, instance):
        if hasattr(self, "menu_cat"):
            self.menu_cat.open()

    def seleccionar_categoria(self, valor):
        self.categoria_seleccionada = valor
        self.btn_categoria.text = valor
        self.menu_cat.dismiss()

    def guardar_registro(self, instance):
        monto_str = self.txt_monto.text.strip()
        if (
            not monto_str
            or not self.tipo_seleccionado
            or not self.categoria_seleccionada
        ):
            return

        try:
            monto = float(monto_str)
        except ValueError:
            return

        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.db.insertar_movimiento(
            self.tipo_seleccionado,
            self.categoria_seleccionada,
            monto,
            fecha_actual,
        )

        self.txt_monto.text = ""
        self.actualizar_ui()

    def actualizar_ui(self):
        ingresos, gastos, balance = self.db.obtener_balance()
        self.lbl_balance.text = f"Balance: ${balance:,.2f}"
        self.lbl_resumen.text = (
            f"Ingresos: ${ingresos:,.2f} | Gastos: ${gastos:,.2f}"
        )

        self.lista_movimientos.clear_widgets()
        for tipo, cat, monto, fecha in self.db.obtener_movimientos():
            icono = (
                "arrow-up-circle-outline"
                if tipo == "Ingreso"
                else "arrow-down-circle-outline"
            )
            item = TwoLineAvatarListItem(
                text=f"{cat} - ${monto:,.2f}",
                secondary_text=f"{tipo} | {fecha}",
            )
            item.add_widget(IconLeftWidget(icon=icono))
            self.lista_movimientos.add_widget(item)


if __name__ == "__main__":
    FinanceApp().run()