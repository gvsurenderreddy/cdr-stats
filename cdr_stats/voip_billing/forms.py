#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2013 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from common.common_functions import isint
from voip_billing.function_def import rate_range
from voip_billing.models import VoIPPlan, VoIPRetailPlan,\
    VoIPCarrierPlan
from voip_billing.constants import CONFIRMATION_TYPE, EXPORT_CHOICE
from cdr.forms import sw_list_with_all, CdrSearchForm


class HorizRadioRenderer(forms.RadioSelect.renderer):
    """This overrides widget method to put radio buttons horizontally
       instead of vertically.
    """
    def render(self):
            """Outputs radios"""
            return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))


def voip_plan_list():
    """Return List of VoIP Plans"""
    return VoIPPlan.objects.values_list('id', 'name').all()


def carrier_plan_list():
    """List all carrier plan"""
    return VoIPCarrierPlan.objects.values_list('id', 'name').all()


def retail_plan_list():
    """List all retail plan"""
    return VoIPRetailPlan.objects.values_list('id', 'name').all()


class FileImport(forms.Form):
    """
    General Form : CSV file upload
    """
    csv_file = forms.FileField(label=_("upload CSV File "), required=True,
                            error_messages={'required': 'please upload File'},
                            help_text=_("browse CSV file"))

    def clean_file(self):
        """
        Form Validation :  File extension Check
        """
        filename = self.cleaned_data["csv_file"]
        file_exts = ("csv", "txt")
        if not str(filename).split(".")[1].lower() in file_exts:
            raise forms.ValidationError(_(u'document types accepted: %s' %
                                        ' '.join(file_exts)))
        else:
            return filename


class RetailRate_fileImport(FileImport):
    """
    Admin Form : Import CSV file with Retail Plan
    """
    plan_id = forms.ChoiceField(label=_("retail plan"), required=False,
        choices=retail_plan_list(), help_text=_("select retail plan"))


class CarrierRate_fileImport(FileImport):
    """
    Admin Form : Import CSV file with Carrier Plan
    """
    plan_id = forms.ChoiceField(label=_("carrier plan"), required=False,
                                choices=carrier_plan_list(),
                                help_text=_("select carrier plan"))
    chk = forms.BooleanField(label=_("make retail plan"), required=False,
                        help_text=_("select if you want to make retail plan"))
    retail_plan_id = forms.ChoiceField(label=_("retail plan"), required=False,
                                choices=retail_plan_list(),
                                help_text=_("select retail plan"))
    profit_percentage = forms.CharField(label=_("profit in % :"), required=False,
                    widget=forms.TextInput(attrs={'size': 3}),
                    help_text=_("enter digit without %"))

    def clean_profit_percentage(self):
        """
        Validation Check:
        Percentage Value must be in digit (int/float)
        """
        chk = self.cleaned_data["chk"]
        p_p = self.cleaned_data["profit_percentage"]
        if chk:
            if not isint(p_p):
                raise forms.ValidationError(_("please enter int/float value"))
            else:
                return p_p


class Exportfile(forms.Form):
    """
    Abstract Form : export file in various format e.g. XLS, CSV, JSON
    """
    export_to = forms.TypedChoiceField(label=_('Export to'), required=True,
                                       choices=list(EXPORT_CHOICE),
                                       widget=forms.RadioSelect(renderer=HorizRadioRenderer))


class Carrier_Rate_fileExport(Exportfile):
    """
    Admin Form : Carrier Rate Export
    """
    plan_id = forms.ChoiceField(label=_("carrier plan"),
                                choices=carrier_plan_list(), required=False)

    def __init__(self, *args, **kwargs):
        super(Carrier_Rate_fileExport, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['plan_id', 'export_to', ]


class Retail_Rate_fileExport(Exportfile):
    """
    Admin Form : Retail Rate Export
    """
    plan_id = forms.ChoiceField(label=_("retail plan"),
                                choices=retail_plan_list(), required=False)

    def __init__(self, *args, **kwargs):
        super(Retail_Rate_fileExport, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['plan_id', 'export_to', ]


class VoIPPlan_fileExport(Exportfile):
    """
    Admin Form : VoIP Plan Export
    """
    plan_id = forms.ChoiceField(label=_("VoIP plan"),
        choices=voip_plan_list(), required=False,
        help_text=_('this will export the VoIPPlan using LCR on each prefix-rate tuple'))

    def __init__(self, *args, **kwargs):
        super(VoIPPlan_fileExport, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['plan_id', 'export_to', ]




class PrefixRetailRrateForm(forms.Form):
    """
    Client Form : To know Retail Rate for prefix
    """
    prefix = forms.CharField(label=_("enter prefix"),
                   widget=forms.TextInput(attrs={'size': 15}), required=False)


class SendVoIPForm(forms.Form):
    """
    Client Form : To Send VoIP
    """
    destination_no = forms.CharField(label=_("destination"), required=True,
                                     help_text=_('enter digit only'))
    txt_msg = forms.CharField(label=_("message"),
                              widget=forms.Textarea,
                              help_text=_('not more than 120 characters'),
                              required=True)

    def clean_destination_no(self):
        """
        Form Validation :  destination_no Check
        """
        destination_no = self.cleaned_data['destination_no']
        if not isint(destination_no):
            raise forms.ValidationError("enter digit only!")
        return destination_no

    def clean_txt_msg(self):
        """
        Form Validation :  text message length Check
        """
        txt_msg = self.cleaned_data['txt_msg']
        if len(txt_msg) > 120:
            raise forms.ValidationError("message should be less than 120 characters !!")
        return txt_msg


class SimulatorForm(SendVoIPForm):
    """
    Admin/Client Form : To Simulator
    """
    plan_id = forms.ChoiceField(label=_("VoIP plan"),
                                choices=voip_plan_list(), required=False)

    def __init__(self, user, *args, **kwargs):
        super(SimulatorForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['plan_id', 'destination_no', ]
        if not user.is_superuser:
            self.fields['plan_id'] = forms.ChoiceField(widget=forms.HiddenInput())

    def clean_plan_id(self):
        """
        Form Validation :  Check Plan id
        """
        plan_id = int(self.cleaned_data['plan_id'])
        if plan_id == 0:
            raise forms.ValidationError("select VoIP Plan!!")
        return plan_id


class CustomRateFilterForm(forms.Form):
    """
    Admin Form : Custom Rate Filter
    """
    rate_range = forms.ChoiceField(label=_(" "),
                                   choices=rate_range(), required=False)
    rate = forms.CharField(label=_(" "),
                           widget=forms.TextInput(attrs={'size': 10}),
                           required=False)


class DailyBillingForm(forms.Form):
    """Daily Billing Form"""
    from_date = forms.CharField(label=_('from'), required=True, max_length=10)
    to_date = forms.CharField(label=_('to'), required=True, max_length=10)
    switch = forms.ChoiceField(label=_('switch'), required=False, choices=sw_list_with_all())

    def __init__(self, *args, **kwargs):
        super(DailyBillingForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_date', 'to_date', 'switch']


class HourlyBillingForm(DailyBillingForm):
    """Hourly Billing Form"""
    def __init__(self, *args, **kwargs):
        super(HourlyBillingForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_date', 'switch']


class RebillForm(CdrSearchForm):
    """Re-bill VoIP call"""
    confirmation = forms.ChoiceField(choices=list(CONFIRMATION_TYPE),
        required=False)

    def __init__(self, *args, **kwargs):
        super(RebillForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['from_date', 'to_date', 'confirmation']
        self.fields['confirmation'].widget = forms.HiddenInput()
