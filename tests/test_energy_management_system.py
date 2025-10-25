import pytest
from datetime import datetime
from src.energy.EnergyManagementSystem import SmartEnergyManagementSystem
from src.energy.DeviceSchedule import DeviceSchedule


class TestEnergyManagementSystem:
    def setup_method(self):
        self.system = SmartEnergyManagementSystem()
        self.base_time = datetime(2024, 1, 1, 12, 0, 0)

    # Testes existentes no arquivo inicial (mantidos com os mesmos nomes e comentários)
    def test_tc1_energy_saving_mode_activated_with_low_priority_devices(self):
        """
        TC1: Modo economia ativado com dispositivos de baixa prioridade.
        Cobertura: Aresta nó 3 → nó 4 (current_price > price_threshold)
        Par def-uso: energy_saving_mode definido (linha 26), usado no retorno
        """
        result = self.system.manage_energy(
            current_price=150.0,
            price_threshold=100.0,
            device_priorities={"Light": 2, "Heating": 1, "TV": 3},
            current_time=self.base_time,
            current_temperature=15.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[]
        )
        assert result.energy_saving_mode is True
        assert result.device_status["Light"] is False
        assert result.device_status["TV"] is False
        assert result.device_status["Heating"] is True

    def test_tc2_no_energy_saving_mode(self):
        """
        TC2: Sem modo economia.
        Cobertura: Aresta nó 3 → nó 6 (current_price <= price_threshold)
        Par def-uso: device_status[device] definido (linha 35), usado posteriormente
        """
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Light": 1, "TV": 2},
            current_time=self.base_time,
            current_temperature=20.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[]
        )
        assert result.energy_saving_mode is False
        assert result.device_status["Light"] is True
        assert result.device_status["TV"] is True

    def test_tc3_night_mode_active(self):
        """
        TC3: Modo noturno ativo (23h).
        Cobertura: Aresta nó 5 → nó 15 (current_time.hour >= 23)
        Par def-uso: device_status modificado para dispositivos não essenciais
        """
        night_time = datetime(2024, 1, 1, 23, 30, 0)
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Light": 1, "TV": 2, "Security": 1, "Refrigerator": 1},
            current_time=night_time,
            current_temperature=20.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[]
        )
        assert result.device_status["Light"] is False
        assert result.device_status["TV"] is False
        assert result.device_status["Security"] is True
        assert result.device_status["Refrigerator"] is True

    def test_tc4_night_mode_early_morning(self):
        """
        TC4: Modo noturno na madrugada (< 6h).
        Cobertura: Aresta nó 5 → nó 15 (current_time.hour < 6)
        """
        early_morning = datetime(2024, 1, 1, 3, 0, 0)
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Light": 1, "Security": 1, "Refrigerator": 1},
            current_time=early_morning,
            current_temperature=20.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[]
        )
        assert result.device_status["Light"] is False
        assert result.device_status["Security"] is True
        assert result.device_status["Refrigerator"] is True

    def test_tc5_low_temperature_heating_activated(self):
        """
        TC5: Temperatura baixa - aquecimento ativado.
        Cobertura: Aresta nó 16 → nó 21 (current_temperature < desired_temperature_range[0])
        Par def-uso: temperature_regulation_active definido (linha 46), usado no retorno
        """
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Heating": 1, "Cooling": 1},
            current_time=self.base_time,
            current_temperature=15.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[]
        )
        assert result.device_status["Heating"] is True
        assert result.temperature_regulation_active is True

    def test_tc6_high_temperature_cooling_activated(self):
        """
        TC6: Temperatura alta - resfriamento ativado.
        Cobertura: Aresta nó 16 → nó 23 → nó 24 (current_temperature > desired_temperature_range[1])
        Par def-uso: device_status["Cooling"] definido (linha 48)
        """
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Heating": 1, "Cooling": 1},
            current_time=self.base_time,
            current_temperature=28.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[]
        )
        assert result.device_status["Cooling"] is True
        assert result.temperature_regulation_active is True

    def test_tc7_ideal_temperature_climate_control_off(self):
        """
        TC7: Temperatura ideal - climatização desligada.
        Cobertura: Aresta nó 23 → nó 26 (temperatura na faixa desejada)
        Par def-uso: device_status["Heating"] e ["Cooling"] definidos como False
        """
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Heating": 1, "Cooling": 1},
            current_time=self.base_time,
            current_temperature=21.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[]
        )
        assert result.device_status["Heating"] is False
        assert result.device_status["Cooling"] is False
        assert result.temperature_regulation_active is False

    def test_tc8_energy_limit_loop_devices_turned_off(self):
        """
        TC8: Loop de limite de energia - dispositivos desligados.
        Cobertura: Aresta nó 27 → nó 28 → nó 31 → nó 32 → nó 35
        Par def-uso: total_energy_used_today modificado (linha 70) e usado (linha 67)
        """
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Light": 2, "TV": 3, "Security": 1},
            current_time=self.base_time,
            current_temperature=20.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=120.0,
            scheduled_devices=[]
        )
        assert result.total_energy_used < 120.0

    def test_tc9_energy_limit_loop_exit_by_limit(self):
        """
        TC9: Loop de limite de energia - saída por atingir limite (break interno).
        Cobertura: Linha 68 (break quando total_energy_used_today < energy_usage_limit)
        """
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Light": 2, "TV": 3, "Radio": 4, "Alarm": 5, "Security": 1, "Heating": 1},
            current_time=self.base_time,
            current_temperature=15.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=102.5,
            scheduled_devices=[]
        )
        assert result.total_energy_used < 100.0

    def test_tc10_energy_limit_loop_no_devices_to_turn_off(self):
        """
        TC10: Loop de limite de energia - sem dispositivos para desligar.
        Cobertura: Aresta nó 28 → nó 30 (not devices_to_turn_off)
        Par def-uso: devices_were_on definido como False (linha 63)
        """
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Security": 1, "Refrigerator": 1},
            current_time=self.base_time,
            current_temperature=20.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=110.0,
            scheduled_devices=[]
        )
        assert result.total_energy_used == 110.0

    def test_tc11_scheduled_devices_correct_time(self):
        """
        TC11: Dispositivos agendados - horário correto.
        Cobertura: Aresta nó 29 → nó 36 → nó 38 (schedule.scheduled_time == current_time)
        Par def-uso: device_status[schedule.device_name] definido (linha 75)
        """
        schedule_time = datetime(2024, 1, 1, 18, 0, 0)
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Light": 2},
            current_time=schedule_time,
            current_temperature=20.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[DeviceSchedule("Light", schedule_time)]
        )
        assert result.device_status["Light"] is True

    def test_tc12_scheduled_devices_different_time(self):
        """
        TC12: Dispositivos agendados - horário diferente.
        Cobertura: Aresta nó 36 → nó 29 (schedule.scheduled_time != current_time)
        """
        current_time = datetime(2024, 1, 1, 18, 0, 0)
        schedule_time = datetime(2024, 1, 1, 19, 0, 0)
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Light": 2},
            current_time=current_time,
            current_temperature=20.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[DeviceSchedule("Light", schedule_time)]
        )
        assert result.device_status["Light"] is True

    def test_tc13_complex_combined_case(self):
        """
        TC13: Caso combinado complexo.
        Cobertura: Múltiplas arestas simultaneamente
        """
        schedule_time = datetime(2024, 1, 1, 23, 30, 0)
        result = self.system.manage_energy(
            current_price=150.0,
            price_threshold=100.0,
            current_time=schedule_time,
            current_temperature=15.0,
            desired_temperature_range=(18.0, 24.0),
            total_energy_used_today=105.0,
            energy_usage_limit=100.0,
            device_priorities={"Light": 2, "Heating": 1, "Security": 1, "TV": 3},
            scheduled_devices=[DeviceSchedule("Radio", schedule_time)]
        )
        assert result.energy_saving_mode is True
        assert result.temperature_regulation_active is True
        assert result.device_status["Heating"] is True
        assert result.device_status["Security"] is True
        assert result.device_status["Radio"] is True
        assert result.device_status["Light"] is False
        assert result.device_status["TV"] is False

    # Testes novos (com comentários explicativos)
    def test_energy_saving_mode_activated_with_price_equal_to_threshold(self):
        """
        Novo Teste: Modo economia ativado com current_price == price_threshold.
        Cobertura: Caso limite onde current_price é exatamente igual ao price_threshold.
        """
        result = self.system.manage_energy(
            current_price=100.0,
            price_threshold=100.0,
            device_priorities={"Light": 2, "TV": 3},
            current_time=self.base_time,
            current_temperature=20.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[]
        )
        assert result.energy_saving_mode is False
        assert result.device_status["Light"] is True
        assert result.device_status["TV"] is True

    def test_night_mode_active_at_6_am(self):
        """
        Novo Teste: Modo noturno ativo às 6h.
        Cobertura: Caso limite onde current_time.hour == 6.
        """
        night_time = datetime(2024, 1, 1, 6, 0, 0)
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Light": 2, "TV": 3, "Security": 1},
            current_time=night_time,
            current_temperature=20.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[]
        )
        assert result.device_status["Light"] is True
        assert result.device_status["TV"] is True
        assert result.device_status["Security"] is True

    def test_night_mode_active_at_6_30_am(self):
        """
        Novo Teste: Modo noturno ativo às 6h30.
        Cobertura: Caso onde current_time.hour == 6 e minutos > 0.
        """
        night_time = datetime(2024, 1, 1, 6, 30, 0)
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Light": 2, "TV": 3, "Security": 1},
            current_time=night_time,
            current_temperature=20.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[]
        )
        assert result.device_status["Light"] is True
        assert result.device_status["TV"] is True
        assert result.device_status["Security"] is True

    def test_heating_not_activated_at_lower_temperature_limit(self):
        """
        Novo Teste: Aquecimento não ativado na temperatura mínima desejada.
        Cobertura: Caso limite onde current_temperature == desired_temperature_range[0].
        """
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Heating": 1, "Cooling": 1},
            current_time=self.base_time,
            current_temperature=18.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[]
        )
        assert result.device_status["Heating"] is False
        assert result.device_status["Cooling"] is False
        assert result.temperature_regulation_active is False

    def test_cooling_not_activated_at_upper_temperature_limit(self):
        """
        Novo Teste: Resfriamento não ativado na temperatura máxima desejada.
        Cobertura: Caso limite onde current_temperature == desired_temperature_range[1].
        """
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Heating": 1, "Cooling": 1},
            current_time=self.base_time,
            current_temperature=24.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[]
        )
        assert result.device_status["Heating"] is False
        assert result.device_status["Cooling"] is False
        assert result.temperature_regulation_active is False

    def test_energy_limit_loop_exit_at_equal_limit(self):
        """
        Novo Teste: Loop de limite de energia - saída quando total_energy_used_today == energy_usage_limit.
        Cobertura: Caso limite onde total_energy_used_today é exatamente igual ao energy_usage_limit.
        """
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Light": 2, "TV": 3},
            current_time=self.base_time,
            current_temperature=20.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=100.0,
            scheduled_devices=[]
        )
        assert result.total_energy_used == 99.0

    def test_device_status_default_behavior(self):
        """
        Novo Teste: Comportamento padrão de device_status.get(device).
        Cobertura: Verifica o comportamento quando device_status não contém o dispositivo.
        """
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Light": 2, "TV": 3},
            current_time=self.base_time,
            current_temperature=20.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[]
        )
        assert result.device_status.get("NonExistentDevice", False) is False
        assert result.device_status.get("Light", False) is True
        assert result.device_status.get("TV", False) is True
        assert "NonExistentDevice" not in result.device_status

    def test_priority_threshold(self):
        """
        Novo Teste: Verifica o comportamento com dispositivos de prioridade 2.
        Cobertura: Caso limite onde priority == 2.
        """
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Light": 2, "TV": 3},
            current_time=self.base_time,
            current_temperature=20.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=120.0,
            scheduled_devices=[]
        )
        assert result.device_status["Light"] is False
        assert result.device_status["TV"] is False

    def test_cooling_device_status_correct_key(self):
        """
        Novo Teste: Verifica se o dispositivo de resfriamento é ativado corretamente.
        Cobertura: Garante que a chave "Cooling" é usada no device_status.
        """
        result = self.system.manage_energy(
            current_price=50.0,
            price_threshold=100.0,
            device_priorities={"Heating": 1, "Cooling": 1},
            current_time=self.base_time,
            current_temperature=28.0,
            desired_temperature_range=(18.0, 24.0),
            energy_usage_limit=100.0,
            total_energy_used_today=50.0,
            scheduled_devices=[]
        )
        assert "Cooling" in result.device_status
        assert result.device_status["Cooling"] is True
        assert "XXCoolingXX" not in result.device_status

