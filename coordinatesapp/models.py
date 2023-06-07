from django.contrib.gis.db import models
from django.utils import timezone


class Place(models.Model):
    text_address = models.CharField(
        'адресс',
        max_length=600,
        unique=True,
    )
    coordinates = models.PointField(
        'координаты'
    )
    last_update_at = models.DateTimeField(
        'дата запроса к геокодеру',
        default=timezone.now,
        db_index=True,
    )

    class Meta:
        verbose_name = 'Место'
        verbose_name_plural = 'Места'

    def __str__(self):
        if len(self.text_address) > 50:
            return f'{self.text_address[:30]}...{self.text_address[-20:]}'
        else:
            return self.text_address
