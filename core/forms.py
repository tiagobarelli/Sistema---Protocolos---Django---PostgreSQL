from datetime import timedelta
from django import forms
from django.contrib.auth import get_user_model
from .models import Tabelionato, TipoAto, Cliente, Protocolo

User = get_user_model()


class SetupMasterForm(forms.ModelForm):
    """Formulário para criação do usuário Master no setup inicial."""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'}),
        label="Senha"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirme a Senha'}),
        label="Confirmação de Senha"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuário (Login)'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-mail'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "As senhas não conferem.")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        # Definições forçadas de segurança para o MASTER
        user.role = User.Role.MASTER
        user.is_superuser = True
        user.is_staff = True
        if commit:
            user.save()
        return user


class UserForm(forms.ModelForm):
    """
    Formulário para criação e edição de usuários.
    - Na criação: senha é obrigatória.
    - Na edição: senha é opcional (se vazia, mantém a atual).
    """
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite a senha',
            'autocomplete': 'new-password'
        }),
        label="Senha",
        required=False,
        help_text="Deixe em branco para manter a senha atual (apenas na edição)."
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme a senha',
            'autocomplete': 'new-password'
        }),
        label="Confirmar Senha",
        required=False
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'role', 'is_active']
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'username': 'Usuário (Login)',
            'email': 'E-mail',
            'role': 'Função',
            'is_active': 'Usuário Ativo',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sobrenome'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'nome.sobrenome'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'role': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se estamos criando um novo usuário, a senha é obrigatória
        if not self.instance.pk:
            self.fields['password'].required = True
            self.fields['password_confirm'].required = True
            self.fields['password'].help_text = "Obrigatório para novos usuários."

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        # Validação de senhas apenas se alguma foi preenchida
        if password or password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', "As senhas não conferem.")
            elif len(password) < 6:
                self.add_error('password', "A senha deve ter pelo menos 6 caracteres.")

        # Se é criação e senha não foi fornecida
        if not self.instance.pk and not password:
            self.add_error('password', "Senha é obrigatória para novos usuários.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        
        # Só atualiza a senha se foi fornecida
        if password:
            user.set_password(password)
        
        # Define is_staff e is_superuser baseado na role
        if user.role == User.Role.MASTER:
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = True  # Permite acesso ao admin
            user.is_superuser = False
        
        if commit:
            user.save()
        return user


# ========== CONFIGURAÇÕES ==========

class TabelionatoForm(forms.ModelForm):
    """Formulário para dados do Tabelionato (Singleton)."""
    
    class Meta:
        model = Tabelionato
        fields = ['denominacao', 'cnpj', 'endereco', 'telefone', 'email', 'site']
        labels = {
            'denominacao': 'Denominação / Razão Social',
            'cnpj': 'CNPJ',
            'endereco': 'Endereço Completo',
            'telefone': 'Telefone',
            'email': 'E-mail',
            'site': 'Website',
        }
        widgets = {
            'denominacao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 1º Tabelionato de Notas de Itápolis'
            }),
            'cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00.000.000/0000-00'
            }),
            'endereco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rua, número, bairro, cidade - UF'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 0000-0000'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contato@tabelionato.com.br'
            }),
            'site': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.exemplo.com.br'
            }),
        }


class TipoAtoForm(forms.ModelForm):
    """
    Formulário para Tipos de Ato.
    O campo tempo_alerta é convertido de dias (int) para timedelta.
    """
    
    tempo_alerta_dias = forms.IntegerField(
        label='Tempo de Alerta (Dias)',
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: 30',
            'min': '0'
        }),
        help_text='Número de dias para o sistema alertar sobre este tipo de ato.'
    )
    
    class Meta:
        model = TipoAto
        fields = ['nome', 'ativo']
        labels = {
            'nome': 'Nome do Tipo de Ato',
            'ativo': 'Ativo',
        }
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Escritura de Compra e Venda'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se estamos editando, converte o timedelta para dias
        if self.instance and self.instance.pk and self.instance.tempo_alerta:
            self.fields['tempo_alerta_dias'].initial = self.instance.tempo_alerta.days
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Converte dias para timedelta
        dias = self.cleaned_data.get('tempo_alerta_dias')
        if dias is not None and dias > 0:
            instance.tempo_alerta = timedelta(days=dias)
        else:
            instance.tempo_alerta = None
        
        if commit:
            instance.save()
        return instance


# ========== CLIENTES ==========

class ClienteForm(forms.ModelForm):
    """
    Formulário para cadastro e edição de Clientes (PF/PJ).
    O campo CPF/CNPJ é mostrado dinamicamente via JavaScript no template.
    """
    
    class Meta:
        model = Cliente
        fields = ['nome', 'tipo_pessoa', 'cpf', 'cnpj', 'telefone', 'email', 'endereco']
        labels = {
            'nome': 'Nome Completo / Razão Social',
            'tipo_pessoa': 'Tipo de Pessoa',
            'cpf': 'CPF',
            'cnpj': 'CNPJ',
            'telefone': 'Telefone',
            'email': 'E-mail',
            'endereco': 'Endereço Completo',
        }
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo ou razão social'
            }),
            'tipo_pessoa': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_tipo_pessoa'
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000.000.000-00',
                'data-mask': 'cpf'
            }),
            'cnpj': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '00.000.000/0000-00',
                'data-mask': 'cnpj'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'endereco': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Rua, número, bairro, cidade - UF, CEP',
                'rows': 3
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campos CPF e CNPJ são opcionais no form (validação é feita no clean)
        self.fields['cpf'].required = False
        self.fields['cnpj'].required = False
    
    def _limpar_documento(self, valor):
        """Remove pontuação de CPF/CNPJ, mantendo apenas números."""
        if valor:
            import re
            return re.sub(r'\D', '', valor)
        return valor
    
    def clean_cpf(self):
        """Limpa pontuação do CPF antes de salvar."""
        cpf = self.cleaned_data.get('cpf')
        return self._limpar_documento(cpf) if cpf else None
    
    def clean_cnpj(self):
        """Limpa pontuação do CNPJ antes de salvar."""
        cnpj = self.cleaned_data.get('cnpj')
        return self._limpar_documento(cnpj) if cnpj else None
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_pessoa = cleaned_data.get('tipo_pessoa')
        cpf = cleaned_data.get('cpf')
        cnpj = cleaned_data.get('cnpj')
        
        # Limpa o campo que não deve ser preenchido baseado no tipo
        if tipo_pessoa == Cliente.TipoPessoa.FISICA:
            # Pessoa Física: precisa de CPF, não pode ter CNPJ
            if not cpf:
                self.add_error('cpf', 'CPF é obrigatório para Pessoa Física.')
            # Limpa CNPJ se preenchido (pode ter sido preenchido antes de trocar o tipo)
            cleaned_data['cnpj'] = None
            
        elif tipo_pessoa == Cliente.TipoPessoa.JURIDICA:
            # Pessoa Jurídica: precisa de CNPJ, não pode ter CPF
            if not cnpj:
                self.add_error('cnpj', 'CNPJ é obrigatório para Pessoa Jurídica.')
            # Limpa CPF se preenchido
            cleaned_data['cpf'] = None
        
        return cleaned_data


class ProtocoloCertidaoForm(forms.ModelForm):
    """
    Formulário para criação/edição de Protocolos do tipo CERTIDÃO.
    
    NOTA: Os campos 'clientes', 'advogados' e 'lista_documentos' são 
    manipulados manualmente via JavaScript e processados na View,
    não fazem parte deste form.
    """

    class Meta:
        model = Protocolo
        fields = [
            'tipo_ato',
            'data_agendamento',
            'horario_agendamento',
            'responsavel',
            'deposito_previo',
            'observacoes',
        ]
        labels = {
            'tipo_ato': 'Tipo de Certidão',
            'data_agendamento': 'Data de Entrega',
            'horario_agendamento': 'Horário',
            'responsavel': 'Responsável pelo Protocolo',
            'deposito_previo': 'Depósito Prévio (R$)',
            'observacoes': 'Observações',
        }
        widgets = {
            'tipo_ato': forms.Select(attrs={
                'class': 'form-select'
            }),
            'data_agendamento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'horario_agendamento': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'responsavel': forms.Select(attrs={
                'class': 'form-select'
            }),
            'deposito_previo': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações adicionais sobre o pedido de certidão...'
            }),
        }

    def __init__(self, *args, **kwargs):
        # Extrai o user do kwargs se fornecido (para definir valor inicial)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtra apenas tipos de ato ativos
        self.fields['tipo_ato'].queryset = TipoAto.objects.filter(ativo=True)
        
        # Configura o campo responsavel com queryset de usuários ativos
        # Usa label_from_instance para exibir apenas o nome, sem o role
        class ResponsavelChoiceField(forms.ModelChoiceField):
            def label_from_instance(self, obj):
                """Retorna apenas o nome completo ou username, sem o role."""
                if obj.get_full_name():
                    return obj.get_full_name()
                return obj.username
        
        self.fields['responsavel'] = ResponsavelChoiceField(
            queryset=User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username'),
            widget=forms.Select(attrs={
                'class': 'form-select'
            }),
            label='Responsável pelo Protocolo',
            required=True,
            empty_label='Selecione o responsável...'
        )
        
        # Define valor inicial como o usuário atual na criação
        if self.user and not self.instance.pk:
            self.fields['responsavel'].initial = self.user
        
        # Campos opcionais
        self.fields['data_agendamento'].required = False
        self.fields['horario_agendamento'].required = False
        self.fields['observacoes'].required = False