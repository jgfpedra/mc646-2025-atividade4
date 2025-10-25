import pytest
from datetime import datetime, timedelta
from src.fraud.FraudDetectionSystem import FraudDetectionSystem
from src.fraud.Transaction import Transaction


class TestFraudDetectionSystem:
    def setup_method(self):
        self.system = FraudDetectionSystem()
        self.base_time = datetime(2024, 1, 1, 12, 0, 0)

    def test_tc23_normal_transaction_no_flags(self):
        """
        TC23: Transação normal sem flags.
        Cobertura: Fluxo básico sem ativar nenhuma condição de fraude
        Par def-uso: risk_score inicializado (linha 21), usado no retorno (linha 76)
        """
        current_transaction = Transaction(
            amount=1000.0,
            timestamp=self.base_time,
            location="São Paulo"
        )
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=[],
            blacklisted_locations=[]
        )
        assert result.is_fraudulent is False
        assert result.is_blocked is False
        assert result.verification_required is False
        assert result.risk_score == 0

    def test_tc24_high_value_transaction(self):
        """
        TC24: Transação de alto valor.
        Cobertura: Aresta nó 4 → nó 5 (amount > 10000)
        Par def-uso: is_fraudulent definido (linha 27), risk_score modificado (linha 28)
        """
        current_transaction = Transaction(
            amount=15000.0,
            timestamp=self.base_time,
            location="São Paulo"
        )
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=[],
            blacklisted_locations=[]
        )
        assert result.is_fraudulent is True
        assert result.verification_required is True
        assert result.risk_score == 50

    def test_tc25_recent_transactions_within_hour(self):
        """
        TC25: Transações recentes dentro de 1 hora.
        Cobertura: Aresta nó 6 → nó 9 → nó 10 (recent_count calculado)
        Par def-uso: recent_count definido (linha 35), usado (linha 37)
        """
        previous_transactions = [
            Transaction(amount=100.0, timestamp=self.base_time - timedelta(minutes=30), location="SP"),
            Transaction(amount=200.0, timestamp=self.base_time - timedelta(minutes=45), location="SP"),
        ]
        current_transaction = Transaction(
            amount=300.0,
            timestamp=self.base_time,
            location="SP"
        )
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=previous_transactions,
            blacklisted_locations=[]
        )
        assert result.is_blocked is False
        assert result.risk_score == 0
        assert result.is_fraudulent is False
        assert result.verification_required is False

    def test_tc26_old_transactions_not_counted(self):
        """
        TC26: Transações antigas não contadas.
        Cobertura: Aresta nó 8 → nó 9 (time_diff >= 60)
        Verifica que transações fora da janela de 60 minutos não afetam recent_count
        """
        previous_transactions = [
            Transaction(amount=100.0, timestamp=self.base_time - timedelta(hours=2), location="SP"),
        ]
        current_transaction = Transaction(
            amount=300.0,
            timestamp=self.base_time,
            location="SP"
        )
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=previous_transactions,
            blacklisted_locations=[]
        )
        assert result.is_blocked is False
        assert result.risk_score == 0
        assert result.is_fraudulent is False
        assert result.verification_required is False

    def test_tc27_excessive_recent_transactions(self):
        """
        TC27: Transações recentes excessivas.
        Cobertura: Aresta nó 10 → nó 11 (recent_count > 10)
        Par def-uso: is_blocked definido (linha 39), risk_score modificado (linha 40)
        """
        previous_transactions = [
            Transaction(
                amount=100.0,
                timestamp=self.base_time - timedelta(minutes=i),
                location="SP"
            )
            for i in range(5, 17)
        ]
        current_transaction = Transaction(
            amount=300.0,
            timestamp=self.base_time,
            location="SP"
        )
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=previous_transactions,
            blacklisted_locations=[]
        )
        assert result.is_blocked is True
        assert result.risk_score == 30
        assert result.is_fraudulent is False
        assert result.verification_required is False

    def test_tc28_rapid_location_change(self):
        """
        TC28: Mudança rápida de localização.
        Cobertura: Aresta nó 12 → nó 13 → nó 16 → nó 17 (locations diferentes + < 30 minutos)
        Par def-uso: is_fraudulent modificado (linha 52), risk_score incrementado (linha 53)
        """
        previous_transactions = [
            Transaction(
                amount=100.0,
                timestamp=self.base_time - timedelta(minutes=10),
                location="São Paulo"
            )
        ]
        current_transaction = Transaction(
            amount=300.0,
            timestamp=self.base_time,
            location="Rio de Janeiro"
        )
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=previous_transactions,
            blacklisted_locations=[]
        )
        assert result.is_fraudulent is True
        assert result.verification_required is True
        assert result.risk_score == 20

    def test_tc29_location_change_sufficient_time(self):
        """
        TC29: Mudança de localização com tempo suficiente.
        Cobertura: Aresta nó 16 → nó 12 (time_diff >= 30)
        Verifica que mudanças de localização após 30+ minutos não causam flag
        """
        previous_transactions = [
            Transaction(
                amount=100.0,
                timestamp=self.base_time - timedelta(hours=1),
                location="São Paulo"
            )
        ]
        current_transaction = Transaction(
            amount=300.0,
            timestamp=self.base_time,
            location="Rio de Janeiro"
        )
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=previous_transactions,
            blacklisted_locations=[]
        )
        assert result.is_fraudulent is False
        assert result.verification_required is False
        assert result.risk_score == 0

    def test_tc30_blacklisted_location(self):
        """
        TC30: Localização na lista negra.
        Cobertura: Aresta nó 18 → nó 19 (location in blacklisted_locations)
        Par def-uso: is_blocked modificado (linha 60), risk_score modificado (linha 61)
        """
        current_transaction = Transaction(
            amount=1000.0,
            timestamp=self.base_time,
            location="País Bloqueado"
        )
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=[],
            blacklisted_locations=["País Bloqueado"]
        )
        assert result.is_blocked is True
        assert result.risk_score == 100

    def test_tc31_multiple_fraud_conditions_accumulate(self):
        """
        TC31: Múltiplas condições de fraude acumulam.
        Cobertura: Múltiplas arestas (alto valor + transações recentes + mudança rápida)
        Testa acumulação de risk_score através de diferentes condições
        """
        previous_transactions = [
            Transaction(
                amount=100.0,
                timestamp=self.base_time - timedelta(minutes=i),
                location="São Paulo"
            )
            for i in range(5, 17)
        ]
        previous_transactions.append(
            Transaction(
                amount=100.0,
                timestamp=self.base_time - timedelta(minutes=5),
                location="Curitiba"
            )
        )
        current_transaction = Transaction(
            amount=15000.0,
            timestamp=self.base_time,
            location="Porto Alegre"
        )
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=previous_transactions,
            blacklisted_locations=[]
        )
        assert result.is_fraudulent is True
        assert result.is_blocked is True
        assert result.verification_required is True
        assert result.risk_score == 100  # 50 + 30 + 20

    def test_edge_case_exact_10_transactions(self):
        """
        Novo Teste: Verifica o caso limite onde há exatamente 10 transações recentes.
        """
        previous_transactions = [
            Transaction(
                amount=100.0,
                timestamp=self.base_time - timedelta(minutes=i),
                location="SP"
            )
            for i in range(1, 11)
        ]
        current_transaction = Transaction(
            amount=300.0,
            timestamp=self.base_time,
            location="SP"
        )
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=previous_transactions,
            blacklisted_locations=[]
        )
        assert result.is_blocked is False

    def test_edge_case_exact_30_minutes(self):
        """
        Novo Teste: Verifica o caso limite onde a mudança de localização ocorre exatamente aos 30 minutos.
        """
        previous_transactions = [
            Transaction(
                amount=100.0,
                timestamp=self.base_time - timedelta(minutes=30),
                location="São Paulo"
            )
        ]
        current_transaction = Transaction(
            amount=300.0,
            timestamp=self.base_time,
            location="Rio de Janeiro"
        )
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=previous_transactions,
            blacklisted_locations=[]
        )
        assert result.is_fraudulent is False
        assert result.verification_required is False
        assert result.risk_score == 0

    def test_edge_case_exact_10000_amount(self):
        """
        Novo Teste: Verifica o caso limite onde o valor da transação é exatamente R$ 10.000.
        """
        current_transaction = Transaction(
            amount=10000.0,
            timestamp=self.base_time,
            location="São Paulo"
        )
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=[],
            blacklisted_locations=[]
        )
        assert result.is_fraudulent is False
        assert result.verification_required is False
        assert result.risk_score == 0
        assert result.is_blocked is False

    def test_amount_exact_10001_should_be_flagged(self):
        """
        Novo Teste: Verifica que uma transação de R$ 10.001 é sinalizada como fraudulenta.
        """
        current_transaction = Transaction(
            amount=10001.0,
            timestamp=self.base_time,
            location="São Paulo"
        )
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=[],
            blacklisted_locations=[]
        )
        assert result.is_fraudulent is True
        assert result.verification_required is True
        assert result.risk_score == 50

    def test_61_minutes_old_transaction_not_counted_towards_recent_limit(self):
        """
        Novo Teste: Verifica que transações com mais de 60 minutos não são contadas no limite de transações recentes.
        """
        previous_transactions = [
            Transaction(amount=10.0, timestamp=self.base_time - timedelta(minutes=i), location="SP")
            for i in range(1, 11)
        ]
        previous_transactions.append(
            Transaction(amount=10.0, timestamp=self.base_time - timedelta(minutes=61), location="SP")
        )
        current_transaction = Transaction(amount=5.0, timestamp=self.base_time, location="SP")
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=previous_transactions,
            blacklisted_locations=[]
        )
        assert result.is_blocked is False
        assert result.risk_score == 0

    def test_60_minutes_exact_is_counted_towards_recent_limit(self):
        """
        Novo Teste: Verifica que transações com exatamente 60 minutos são contadas no limite de transações recentes.
        """
        previous_transactions = [
            Transaction(amount=10.0, timestamp=self.base_time - timedelta(minutes=i), location="SP")
            for i in range(1, 11)
        ]
        previous_transactions.append(
            Transaction(amount=10.0, timestamp=self.base_time - timedelta(minutes=60), location="SP")
        )
        current_transaction = Transaction(amount=5.0, timestamp=self.base_time, location="SP")
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=previous_transactions,
            blacklisted_locations=[]
        )
        assert result.is_blocked is True
        assert result.risk_score == 30

    def test_high_amount_accumulates_with_prior_recent_risk(self):
        """
        Novo Teste: Verifica que o risco acumula quando há transações recentes excessivas e valor alto.
        """
        previous_transactions = [
            Transaction(
                amount=10.0,
                timestamp=self.base_time - timedelta(minutes=i),
                location="SP"
            ) for i in range(1, 12)
        ]
        current_transaction = Transaction(
            amount=15000.0,
            timestamp=self.base_time,
            location="SP"
        )
        result = self.system.check_for_fraud(
            current_transaction=current_transaction,
            previous_transactions=previous_transactions,
            blacklisted_locations=[]
        )
        assert result.risk_score == 80
