from django import forms

from .models import LawyerAction


class LawyerActionCreateForm(forms.ModelForm):
    class Meta:
        model = LawyerAction
        fields = [
            'acao',
            'valor_acordo',
            'resultado_macro',
            'resultado_micro',
            'valor_condenacao',
        ]
        widgets = {
            'acao': forms.Select(attrs={'id': 'id_acao'}),
            'valor_acordo': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'valor_condenacao': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['valor_acordo'].required = False
        self.fields['resultado_macro'].required = False
        self.fields['resultado_micro'].required = False
        self.fields['valor_condenacao'].required = False

    def clean(self):
        cleaned_data = super().clean()
        acao = cleaned_data.get('acao')
        valor_acordo = cleaned_data.get('valor_acordo')
        resultado_macro = cleaned_data.get('resultado_macro')
        resultado_micro = cleaned_data.get('resultado_micro')
        valor_condenacao = cleaned_data.get('valor_condenacao')

        if acao == 'PROPOR_ACORDO':
            if valor_acordo is None:
                self.add_error('valor_acordo', 'Informe o valor do acordo para PROPOR_ACORDO.')
            cleaned_data['resultado_macro'] = None
            cleaned_data['resultado_micro'] = None
            cleaned_data['valor_condenacao'] = None

        if acao == 'DEFENDER':
            if not resultado_macro:
                self.add_error('resultado_macro', 'Informe o resultado macro para DEFENDER.')
            if not resultado_micro:
                self.add_error('resultado_micro', 'Informe o resultado micro para DEFENDER.')
            if valor_condenacao is None:
                self.add_error('valor_condenacao', 'Informe o valor da condenacao para DEFENDER.')
            cleaned_data['valor_acordo'] = None

        if acao not in {'PROPOR_ACORDO', 'DEFENDER'}:
            cleaned_data['valor_acordo'] = None
            cleaned_data['resultado_macro'] = None
            cleaned_data['resultado_micro'] = None
            cleaned_data['valor_condenacao'] = None

        return cleaned_data
