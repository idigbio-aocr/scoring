from django.db import models

# Create your models here.
class Dataset(models.Model):
    name = models.CharField(max_length=30)
    
    def __unicode__(self):
        return "{0} {1}".format(self.id, self.name)

class Image(models.Model):
    name = models.CharField(max_length=100)
    dataset = models.ForeignKey(Dataset)
    uuid = models.CharField(max_length=40)
    humantext = models.TextField()
    silverparse = models.TextField()
    goldparse = models.TextField()
    
    def __unicode__(self):
        return "{0} {1} {2}".format(self.id, self.name, self.uuid[:10])
    
class OcrSubmission(models.Model):
    image = models.ForeignKey(Image)
    user = models.CharField(max_length=100)
    software = models.CharField(max_length=255)
    score = models.FloatField()
    text = models.TextField(blank=True)
    result = models.TextField()
    
    def get_fields(self):
        # make a list of field/values.
        return [(field, field.value_to_string(self)) for field in self._meta.fields]
        
    @models.permalink
    def get_absolute_url(self):
        return ('scoring.views.view_ocr', (),{"ocr_id": str(self.id)})        
    
class ParsedSubmission(models.Model):
    image = models.ForeignKey(Image)
    user = models.CharField(max_length=100)
    software = models.CharField(max_length=255)
    parse_type = models.CharField(max_length=10)
    score = models.FloatField()
    text = models.TextField(blank=True)
    result = models.TextField()
    
    def get_fields(self):
        # make a list of field/values.
        return [(field, field.value_to_string(self)) for field in self._meta.fields]
        
    @models.permalink
    def get_absolute_url(self):
        return ('scoring.views.view_parse', (),{"parse_id": str(self.id)})        