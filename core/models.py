import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField

# 1. USUÁRIOS PERSONALIZADOS
class User(AbstractUser):
    class Role(models.TextChoices):
        MASTER = 'MASTER', 'Master'
        ADMINISTRATIVO = 'ADMINISTRATIVO', 'Administrativo'
        ESCREVENTE = 'ESCREVENTE', 'Escrevente'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ESCREVENTE,
        verbose_name="Função"
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# 2. TABELIONATO (SINGLETON)
class Tabelionato(models.Model):
    denominacao = models.CharField(max_length=255, verbose_name="Denominação")
    cnpj = models.CharField(max_length=18, verbose_name="CNPJ")
    endereco = models.CharField(max_length=255, verbose_name="Endereço")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    email = models.EmailField(verbose_name="E-mail")
    site = models.URLField(blank=True, null=True, verbose_name="Site")

    def save(self, *args, **kwargs):
        if not self.pk and Tabelionato.objects.exists():
            raise ValidationError("Apenas um registro de Tabelionato é permitido (Padrão Singleton).")
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.denominacao

    class Meta:
        verbose_name = "Configuração do Tabelionato"
        verbose_name_plural = "Configuração do Tabelionato"


# 3. TIPO DE ATO
class TipoAto(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome do Ato")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    # DurationField é ideal para cálculos de tempo (ex: alertas de vencimento)
    tempo_alerta = models.DurationField(
        help_text="Tempo padrão para alerta (ex: DD HH:MM:SS)", 
        null=True, 
        blank=True
    )

    def __str__(self):
        return self.nome


# 4. CLIENTE (UNIFICAÇÃO PF/PJ)
class Cliente(models.Model):
    class TipoPessoa(models.TextChoices):
        FISICA = 'FISICA', 'Pessoa Física'
        JURIDICA = 'JURIDICA', 'Pessoa Jurídica'

    nome = models.CharField(max_length=255, verbose_name="Nome Completo / Razão Social")
    tipo_pessoa = models.CharField(max_length=10, choices=TipoPessoa.choices, default=TipoPessoa.FISICA)
    
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True, verbose_name="CPF")
    cnpj = models.CharField(max_length=18, unique=True, null=True, blank=True, verbose_name="CNPJ")
    
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    endereco = models.TextField(verbose_name="Endereço Completo", blank=True, null=True)

    def clean(self):
        # Validação cruzada baseada no Tipo de Pessoa
        if self.tipo_pessoa == self.TipoPessoa.FISICA:
            if not self.cpf:
                raise ValidationError("CPF é obrigatório para Pessoa Física.")
            if self.cnpj:
                raise ValidationError("Pessoa Física não deve ter CNPJ preenchido.")
        
        if self.tipo_pessoa == self.TipoPessoa.JURIDICA:
            if not self.cnpj:
                raise ValidationError("CNPJ é obrigatório para Pessoa Jurídica.")
            if self.cpf:
                raise ValidationError("Pessoa Jurídica não deve ter CPF preenchido.")

    def save(self, *args, **kwargs):
        self.full_clean() # Garante que o clean() seja chamado antes de salvar
        super().save(*args, **kwargs)

    def __str__(self):
        doc = self.cpf if self.tipo_pessoa == self.TipoPessoa.FISICA else self.cnpj
        return f"{self.nome} ({doc})"


# 5. PROTOCOLO (CORE)
class Protocolo(models.Model):
    class TipoProtocolo(models.TextChoices):
        ATO_NOTARIAL = 'ATO_NOTARIAL', 'Ato Notarial'
        CERTIDAO = 'CERTIDAO', 'Certidão'

    class StatusProtocolo(models.TextChoices):
        EM_ANDAMENTO = 'EM_ANDAMENTO', 'Em Andamento'
        ESCRITURA_FINALIZADA = 'ESCRITURA_FINALIZADA', 'Escritura Finalizada'
        CONCLUIDO = 'CONCLUIDO', 'Concluído'
        CANCELADO = 'CANCELADO', 'Cancelado'

    # Campos de Identificação
    numero_protocolo = models.CharField(max_length=50, unique=True, verbose_name="Número do Protocolo")
    hash_acesso_publico = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Classificação
    tipo = models.CharField(max_length=20, choices=TipoProtocolo.choices, default=TipoProtocolo.ATO_NOTARIAL)
    status = models.CharField(max_length=25, choices=StatusProtocolo.choices, default=StatusProtocolo.EM_ANDAMENTO)
    tipo_ato = models.ForeignKey(TipoAto, on_delete=models.PROTECT, verbose_name="Tipo de Ato")

    # Datas e Valores
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_agendamento = models.DateField(null=True, blank=True, verbose_name="Data Agendamento")
    horario_agendamento = models.TimeField(null=True, blank=True, verbose_name="Horário")
    deposito_previo = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Depósito Prévio")

    # Detalhes
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações Gerais")
    observacoes_ato_notarial = models.TextField(blank=True, null=True, verbose_name="Obs. Específica Ato Notarial")
    
    # Lista de Documentos (PostgreSQL ArrayField)
    lista_documentos = ArrayField(
        models.CharField(max_length=255),
        blank=True,
        default=list,
        verbose_name="Lista de Documentos Entregues"
    )

    # Relacionamentos
    criado_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='protocolos_criados')
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='protocolos_responsavel')
    
    clientes = models.ManyToManyField(Cliente, related_name='protocolos_como_cliente', verbose_name="Clientes Envolvidos")
    advogados = models.ManyToManyField(Cliente, related_name='protocolos_como_advogado', blank=True, verbose_name="Advogados")

    def __str__(self):
        return f"Prot: {self.numero_protocolo} - {self.get_status_display()}"


# 6. DADOS ESCRITURA (EXTENSÃO)
class DadosEscritura(models.Model):
    protocolo = models.OneToOneField(Protocolo, on_delete=models.CASCADE, primary_key=True, related_name='dados_escritura')
    
    livro = models.CharField(max_length=20, verbose_name="Livro")
    folha = models.CharField(max_length=20, verbose_name="Folha")
    data_escritura = models.DateField(verbose_name="Data da Escritura")
    
    comunicacao_coaf = models.BooleanField(default=False, verbose_name="Comunicação COAF?")
    relatorio_coaf = models.TextField(blank=True, null=True, verbose_name="Relatório COAF")
    data_comunicacao_coaf = models.DateField(blank=True, null=True)
    numero_comunicacao_coaf = models.CharField(max_length=50, blank=True, null=True)
    
    documentos_digitalizados = models.BooleanField(default=False, verbose_name="Docs. Digitalizados")
    emolumentos = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Emolumentos")
    finalizado = models.BooleanField(default=False)

    def __str__(self):
        return f"Escritura do Protocolo {self.protocolo.numero_protocolo}"


# 7. IMÓVEL
class Imovel(models.Model):
    protocolo = models.ForeignKey(Protocolo, on_delete=models.CASCADE, related_name='imoveis')
    
    cadastro_municipal = models.CharField(max_length=50, verbose_name="Cadastro Municipal / IPTU")
    valor_venal = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor Venal")
    valor_negocio = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor do Negócio")
    descricao = models.TextField(verbose_name="Descrição do Imóvel")

    def __str__(self):
        return f"Imóvel: {self.cadastro_municipal}"


# 8. LOGS E JUSTIFICATIVAS
class ComentarioInterno(models.Model):
    protocolo = models.ForeignKey(Protocolo, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    texto = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentário em {self.protocolo} por {self.usuario}"

class JustificativaCancelamento(models.Model):
    protocolo = models.OneToOneField(Protocolo, on_delete=models.CASCADE, related_name='justificativa_cancelamento')
    motivo = models.TextField()
    data_cancelamento = models.DateTimeField(auto_now_add=True)
    cancelado_por = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return f"Cancelamento Prot: {self.protocolo.numero_protocolo}"