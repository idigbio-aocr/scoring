from django import forms
from django.forms import ModelForm

from django.contrib.auth.forms import AuthenticationForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions

from scoring.models import *

class OcrSubmissionForm(ModelForm):
    class Meta:
        model = OcrSubmission
        fields = ('user', 'software', 'text')
        
    file = forms.FileField(label="Chose a File to Upload", required=False)
        
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-OcrSubmissionForm'
        self.helper.form_method = 'post'

        self.helper.add_input(Submit('submit', 'Submit OCR'))
        super(OcrSubmissionForm, self).__init__(*args, **kwargs)  
        
class ParsedSubmissionForm(ModelForm):
    class Meta:
        model = ParsedSubmission
        fields = ('user', 'software', 'text')
        
    file = forms.FileField(label="Chose a File to Upload", required=False)
        
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-ParseSubmissionForm'
        self.helper.form_method = 'post'        

        self.helper.add_input(Submit('submit', 'Submit Parse'))
        super(ParsedSubmissionForm, self).__init__(*args, **kwargs)          