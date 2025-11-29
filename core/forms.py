from django import forms
from django.contrib.auth import get_user_model

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