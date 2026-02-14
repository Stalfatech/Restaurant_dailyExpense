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
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


   

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
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
        }
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
            'category': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'purchase_type': forms.Select(attrs={'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
'invoice': forms.FileInput(attrs={'id': 'invoiceInput', 'class': 'form-control'}),
'amount': forms.NumberInput(attrs={'id': 'amountField', 'class': 'form-control'}),


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
        self.fields['amount'].required = False
        mandatory_fields = ['date', 'category', 'supplier', 'product', 'purchase_type', 'invoice']
        for field_name in mandatory_fields:
            

            self.fields[field_name].widget.attrs['required'] = 'true'

        if user and user.user_type != 0:
            # Manager: hide branch and status fields
            self.fields['branch'].required = False
            self.fields['status'].required = False
            self.fields['branch'].widget = forms.HiddenInput()
            self.fields['status'].widget = forms.HiddenInput()
            
            
from .models import DailySale

class DailySaleForm(forms.ModelForm):
    class Meta:
        model = DailySale
        fields = [
            'date',
             'branch',
            'breakfast',
            'lunch',
            'dinner',
            'delivery',
            'pos_amount',
            'pos_type',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'breakfast': forms.NumberInput(attrs={'class': 'form-control'}),
            'lunch': forms.NumberInput(attrs={'class': 'form-control'}),
            'dinner': forms.NumberInput(attrs={'class': 'form-control'}),
            'delivery': forms.NumberInput(attrs={'class': 'form-control'}),
            'pos_amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
            user = kwargs.pop('user', None)
            super().__init__(*args, **kwargs)
            if user and user.user_type == 0:
                self.fields['branch'].required = True

            elif user and user.user_type == 1:
                self.fields['branch'].widget = forms.HiddenInput()
                self.fields['branch'].required = False 