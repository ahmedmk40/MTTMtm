"""
Admin configuration for the cases app.
"""

from django.contrib import admin
from .models import Case, CaseTransaction, CaseNote, CaseAttachment, CaseActivity


class CaseTransactionInline(admin.TabularInline):
    model = CaseTransaction
    extra = 0
    readonly_fields = ('added_at',)


class CaseNoteInline(admin.TabularInline):
    model = CaseNote
    extra = 0
    readonly_fields = ('created_at',)


class CaseAttachmentInline(admin.TabularInline):
    model = CaseAttachment
    extra = 0
    readonly_fields = ('uploaded_at',)


class CaseActivityInline(admin.TabularInline):
    model = CaseActivity
    extra = 0
    readonly_fields = ('performed_at',)
    can_delete = False


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('case_id', 'title', 'priority', 'status', 'created_at', 'assigned_to')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('case_id', 'title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'closed_at')
    fieldsets = (
        (None, {
            'fields': ('case_id', 'title', 'description')
        }),
        ('Status', {
            'fields': ('priority', 'status', 'resolution')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'closed_at')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assigned_to')
        }),
        ('Metrics', {
            'fields': ('financial_impact', 'risk_score')
        }),
    )
    inlines = [CaseTransactionInline, CaseNoteInline, CaseAttachmentInline, CaseActivityInline]


@admin.register(CaseTransaction)
class CaseTransactionAdmin(admin.ModelAdmin):
    list_display = ('case', 'transaction_id', 'added_at', 'added_by')
    list_filter = ('added_at',)
    search_fields = ('case__case_id', 'transaction_id')
    readonly_fields = ('added_at',)


@admin.register(CaseNote)
class CaseNoteAdmin(admin.ModelAdmin):
    list_display = ('case', 'content_preview', 'created_at', 'created_by')
    list_filter = ('created_at',)
    search_fields = ('case__case_id', 'content')
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(CaseAttachment)
class CaseAttachmentAdmin(admin.ModelAdmin):
    list_display = ('case', 'filename', 'file_type', 'file_size_display', 'uploaded_at', 'uploaded_by')
    list_filter = ('uploaded_at', 'file_type')
    search_fields = ('case__case_id', 'filename')
    readonly_fields = ('uploaded_at',)
    
    def file_size_display(self, obj):
        """
        Display file size in a human-readable format.
        """
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024 or unit == 'GB':
                return f"{size:.2f} {unit}"
            size /= 1024
    file_size_display.short_description = 'File Size'


@admin.register(CaseActivity)
class CaseActivityAdmin(admin.ModelAdmin):
    list_display = ('case', 'activity_type', 'description_preview', 'performed_at', 'performed_by')
    list_filter = ('activity_type', 'performed_at')
    search_fields = ('case__case_id', 'description')
    readonly_fields = ('performed_at',)
    
    def description_preview(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'
