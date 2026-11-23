from django.utils import timezone


def varsta_ani_luni(data_nasterii):
    """Returnează vârsta în ani și luni deja împlinite."""
    azi = timezone.localdate()
    luni = (azi.year - data_nasterii.year) * 12 + azi.month - data_nasterii.month
    if azi.day < data_nasterii.day:
        luni -= 1
    return divmod(luni, 12)
