from django import forms

class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@gmail.com'
        })
    )

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )



from django import forms
from .models import Branch, Expense, Supplier, Product
from django.core.exceptions import ValidationError


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['branch'].empty_label = "Select Branch"
    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not phone.isdigit():
            raise ValidationError("Phone number must contain digits only.")
        if len(phone) < 8:
            raise ValidationError("Phone number too short.")
        return phone


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.fields['branch'].empty_label = "Select Branch"
            self.fields['supplier'].empty_label = "Select Supplier"


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }
       

    def clean_invoice(self):
        invoice = self.cleaned_data.get('invoice')
        if invoice:
            if not invoice.name.endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise ValidationError("Invoice must be PDF or Image file.")
        return invoice

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        amount = cleaned_data.get('amount')

        if quantity and amount:
            if quantity <= 0:
                raise ValidationError("Quantity must be greater than zero.")
            if amount <= 0:
                raise ValidationError("Amount must be greater than zero.")

        return cleaned_data
