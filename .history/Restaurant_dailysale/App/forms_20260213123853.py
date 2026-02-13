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
        fields = ['name', 'phone']


   

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
        fields = [
            'date', 'category', 'supplier', 'product',
            'quantity', 'purchase_type', 'amount', 'invoice', 'description', 'branch','status'
        ]

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
               'invoice': forms.FileInput(attrs={'id': 'invoiceInput'}),
            'amount': forms.NumberInput(attrs={'id': 'amountField'}),
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
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.user_type != 0:
            # Manager: hide branch and status fields
            self.fields['branch'].required = False
            self.fields['status'].required = False
            self.fields['branch'].widget = forms.HiddenInput()
            self.fields['status'].widget = forms.HiddenInput()