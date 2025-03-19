"""
IP Address models for the Transaction Monitoring and Fraud Detection System.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class IPAddress(models.Model):
    """
    Model for IP address information.
    """
    ip_address = models.CharField(_('IP Address'), max_length=45, primary_key=True)
    country = models.CharField(_('Country'), max_length=100, null=True, blank=True)
    country_code = models.CharField(_('Country Code'), max_length=2, null=True, blank=True)
    region = models.CharField(_('Region'), max_length=100, null=True, blank=True)
    city = models.CharField(_('City'), max_length=100, null=True, blank=True)
    postal_code = models.CharField(_('Postal Code'), max_length=20, null=True, blank=True)
    latitude = models.DecimalField(
        _('Latitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        _('Longitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    
    # ISP information
    isp = models.CharField(_('ISP'), max_length=255, null=True, blank=True)
    asn = models.CharField(_('ASN'), max_length=50, null=True, blank=True)
    organization = models.CharField(_('Organization'), max_length=255, null=True, blank=True)
    
    # Risk indicators
    is_proxy = models.BooleanField(_('Is Proxy'), default=False)
    is_vpn = models.BooleanField(_('Is VPN'), default=False)
    is_tor = models.BooleanField(_('Is Tor Exit Node'), default=False)
    is_hosting = models.BooleanField(_('Is Hosting Provider'), default=False)
    is_suspicious = models.BooleanField(_('Is Suspicious'), default=False)
    is_high_risk = models.BooleanField(_('Is High Risk'), default=False)
    risk_score = models.DecimalField(
        _('Risk Score'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Timestamps
    first_seen = models.DateTimeField(_('First Seen'), auto_now_add=True)
    last_seen = models.DateTimeField(_('Last Seen'), auto_now=True)
    
    # Additional metadata
    metadata = models.JSONField(_('Metadata'), default=dict)
    
    class Meta:
        verbose_name = _('IP Address')
        verbose_name_plural = _('IP Addresses')
        indexes = [
            models.Index(fields=['country_code']),
            models.Index(fields=['is_proxy']),
            models.Index(fields=['is_vpn']),
            models.Index(fields=['is_tor']),
            models.Index(fields=['is_suspicious']),
            models.Index(fields=['is_high_risk']),
        ]
    
    def __str__(self):
        return f"{self.ip_address} ({self.country_code})"
    
    def save(self, *args, **kwargs):
        """
        Override save method to set high risk flag based on risk indicators.
        """
        if self.is_proxy or self.is_vpn or self.is_tor:
            self.is_suspicious = True
            
        if self.risk_score and self.risk_score > 70:
            self.is_high_risk = True
            
        super().save(*args, **kwargs)