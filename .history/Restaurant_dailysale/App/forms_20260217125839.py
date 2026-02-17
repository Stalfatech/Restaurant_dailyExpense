from sys import platform
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
from .models import Branch, DeliverySale, Expense, Supplier, Product
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
            'quantity', 'purchase_type', 'amount',
            'invoice', 'description', 'branch', 'status'
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
           'invoice': forms.FileInput(attrs={
    'id': 'invoiceInput',
    'class': 'form-control'
}),

            'amount': forms.NumberInput(attrs={
                'id': 'amountField',
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['amount'].required = False

        # Mandatory fields except invoice
        mandatory_fields = ['date', 'category', 'supplier', 'product', 'purchase_type']

        for field_name in mandatory_fields:
            self.fields[field_name].widget.attrs['required'] = 'true'

        # 🔥 Invoice required only when creating
        if not self.instance.pk:
            self.fields['invoice'].required = True
            self.fields['invoice'].widget.attrs['required'] = 'true'
        else:
            self.fields['invoice'].required = False

        # Manager restrictions
        if user and user.user_type != 0:
            self.fields['branch'].required = False
            self.fields['status'].required = False
            self.fields['branch'].widget = forms.HiddenInput()
            self.fields['status'].widget = forms.HiddenInput()

    def clean_invoice(self):
        invoice = self.cleaned_data.get('invoice')

        # If editing and no new file uploaded → keep old file
        if not invoice and self.instance.pk:
            return self.instance.invoice

        if invoice:
            if not invoice.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise ValidationError("Invoice must be PDF or Image file.")

        return invoice

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        amount = cleaned_data.get('amount')

        if quantity and quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")

        if amount and amount <= 0:
            raise ValidationError("Amount must be greater than zero.")

        return cleaned_data

class DeliverySaleForm(forms.ModelForm):
    class Meta:
        model = DeliverySale
        fields = ('platform', 'amount')
        widgets = {
            'platform': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        platform = cleaned_data.get('platform')
        amount = cleaned_data.get('amount')

        # ✅ If completely empty → ignore
        if not platform and not amount:
            self.cleaned_data = {}
            return cleaned_data

        # ✅ If partially filled → both required
        if not platform:
            self.add_error('platform', 'Select delivery platform.')

        if not amount:
            self.add_error('amount', 'Enter delivery amount.')
        elif amount <= 0:
            self.add_error('amount', 'Amount must be greater than 0.')

        return cleaned_data


from 
class DailySaleForm(forms.ModelForm):
    class Meta:
        model = DailySale
        fields = [
            'date',
            'branch',
            'pos_amount',
            'pos_type',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'pos_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'pos_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        

        if self.user:

            # 🔹 ADMIN
            if self.user.user_type == 0:
                self.fields['branch'].required = True

            # 🔹 MANAGER
            elif self.user.user_type == 1:
                self.fields['branch'].widget = forms.HiddenInput()
                self.fields['branch'].required = False

                # VERY IMPORTANT: Set branch automatically
                if not self.instance.pk:  # Only for ADD
                    self.initial['branch'] = self.user.branch
   
    def save(self, commit=True):
        instance = super().save(commit=False)

    # Manager always uses their branch
        if self.user and self.user.user_type == 1:
         instance.branch = self.user.branch

        if commit:
          instance.save()

        return instance

class DailySaleItemForm(forms.ModelForm):
    class Meta:
        model = DailySaleItem
        fields = ('meal_type', 'item_name', 'amount')
        widgets = {
            'meal_type': forms.Select(attrs={'class': 'form-select'}),
            'item_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter item name'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        meal_type = cleaned_data.get('meal_type')
        item_name = cleaned_data.get('item_name')
        amount = cleaned_data.get('amount')

        # ✅ If completely empty → ignore
        if not meal_type and not item_name and not amount:
            self.cleaned_data = {}
            return cleaned_data

        # ✅ If partially filled → all required
        if not meal_type:
            self.add_error('meal_type', 'Select meal type.')

        if not item_name:
            self.add_error('item_name', 'Enter item name.')

        if not amount:
            self.add_error('amount', 'Enter amount.')
        elif amount <= 0:
            self.add_error('amount', 'Amount must be greater than 0.')

        return cleaned_data


DailySaleItemFormSet = forms.inlineformset_factory(
    DailySale,
    DailySaleItem,
   form=DailySaleItemForm, 
    extra=1,
    can_delete=True
)


DeliveryFormSet = forms.inlineformset_factory(
    DailySale,
    DeliverySale,
     form=DeliverySaleForm,
    extra=1,
    can_delete=True
)


from django import forms
from .models import DeliveryPlatform

class DeliveryPlatformForm(forms.ModelForm):
    class Meta:
        model = DeliveryPlatform
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Platform Name'
            })
        }

    def clean_name(self):
        name = self.cleaned_data['name'].strip()

        # Only check duplicate when adding (no instance.pk)
        if not self.instance.pk:
            if DeliveryPlatform.objects.filter(name__iexact=name).exists():
                raise forms.ValidationError("This platform already exists ❌")

        return name
