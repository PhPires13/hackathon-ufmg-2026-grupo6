from django import forms

from .models import LawyerAction


class LawyerActionCreateForm(forms.ModelForm):
    class Meta:
        model = LawyerAction
        fields = ['acao', 'valor_acordo']
        widgets = {
            'acao': forms.Select(attrs={'id': 'id_acao'}),
            'valor_acordo': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        acao = cleaned_data.get('acao')
        valor_acordo = cleaned_data.get('valor_acordo')

        if acao == 'PROPOR_ACORDO' and valor_acordo is None:
            self.add_error('valor_acordo', 'Informe o valor do acordo para PROPOR_ACORDO.')

        if acao != 'PROPOR_ACORDO':
            cleaned_data['valor_acordo'] = None

        return cleaned_data

