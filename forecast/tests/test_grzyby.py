from __future__ import annotations

import unittest

from mushboom.grzyby import _parse, intensity_for_county

HEADER_HTML = """
<span>doniesienia <!-- TYTUL-RAPORT-OD-DO -->  11 - 17.wrz 2026<!-- END -->:</span>
<a href="/raporty/wystepowanie-DS.htm"><b>dolnośl.</b> <!-- WOJ-DS -->  (79)<!-- END --></a>
<a href="/raporty/wystepowanie-KP.htm"><b>kuj.-pom.</b> <!-- WOJ-KP -->  (31)<!-- END --></a>
<a href="/raporty/wystepowanie-LB.htm"><b>lubel.</b> <!-- WOJ-LB -->  (19)<!-- END --></a>
<a href="/raporty/wystepowanie-LS.htm"><b>lubus.</b> <!-- WOJ-LS -->  (31)<!-- END --></a>
<a href="/raporty/wystepowanie-LD.htm"><b>łódz.</b> <!-- WOJ-LD -->  (60)<!-- END --></a>
<a href="/raporty/wystepowanie-MP.htm"><b>małopol.</b> <!-- WOJ-MP -->  (44)<!-- END --></a>
<a href="/raporty/wystepowanie-MZ.htm"><b>mazow.</b> <!-- WOJ-MZ -->  (100/109)<!-- END --></a>
<a href="/raporty/wystepowanie-OP.htm"><b>opols.</b> <!-- WOJ-OP -->  (20)<!-- END --></a>
<a href="/raporty/wystepowanie-PK.htm"><b>podkarp.</b> <!-- WOJ-PK -->  (19)<!-- END --></a>
<a href="/raporty/wystepowanie-PL.htm"><b>podlas.</b> <!-- WOJ-PL -->  (9)<!-- END --></a>
<a href="/raporty/wystepowanie-PM.htm"><b>pomor.</b> <!-- WOJ-PM -->  (58)<!-- END --></a>
<a href="/raporty/wystepowanie-SL.htm"><b>śląsk.</b> <!-- WOJ-SL -->  (87)<!-- END --></a>
<a href="/raporty/wystepowanie-SK.htm"><b>św.-krz.</b> <!-- WOJ-SK -->  (16)<!-- END --></a>
<a href="/raporty/wystepowanie-WM.htm"><b>war.-maz.</b> <!-- WOJ-WM -->  (20)<!-- END --></a>
<a href="/raporty/wystepowanie-WP.htm"><b>wlkpl.</b> <!-- WOJ-WP -->  (66)<!-- END --></a>
<a href="/raporty/wystepowanie-ZP.htm"><b>zach.-pom.</b> <!-- WOJ-ZP -->  (33)<!-- END --></a>
<a href="/raporty/wystepowanie-ZX.htm"><b>lokalizacja?</b> <!-- WOJ-ZX -->  (6)<!-- END --></a>
<a href="/raporty/wystepowanie-ZZ.htm"><b>zagranica</b> <!-- WOJ-ZZ --> <!-- END --></a>
<div class="w3-row-padding doniesienie-blok"><div class="w3-medium">woj. pomorskie</div></div>
<div class="w3-row-padding doniesienie-blok"><div class="w3-medium">woj. mazowieckie</div></div>
"""

BLOCKS_ONLY_HTML = """
<div class="w3-row-padding doniesienie-blok"><div class="w3-medium">woj. pomorskie</div></div>
<div class="w3-row-padding doniesienie-blok"><div class="w3-medium">woj. mazowieckie</div></div>
<div class="w3-row-padding doniesienie-blok"><div class="w3-medium">woj. mazowieckie</div></div>
"""


class GrzybyParseTests(unittest.TestCase):
    def test_header_totals_beat_visible_posts(self) -> None:
        parsed = _parse(HEADER_HTML)
        self.assertEqual(parsed["period"], "11 - 17.wrz 2026")
        self.assertEqual(parsed["by_woj"]["dolnośląskie"], 79)
        self.assertEqual(parsed["by_woj"]["mazowieckie"], 109)
        self.assertEqual(parsed["by_woj"]["pomorskie"], 58)
        self.assertEqual(parsed["unknown_location"], 6)
        self.assertEqual(parsed["report_total"], 707)
        self.assertGreater(parsed["report_total"], 50)

    def test_falls_back_to_visible_blocks_without_header(self) -> None:
        parsed = _parse(BLOCKS_ONLY_HTML)
        self.assertEqual(parsed["by_woj"]["pomorskie"], 1)
        self.assertEqual(parsed["by_woj"]["mazowieckie"], 2)
        self.assertEqual(parsed["report_total"], 3)
        self.assertIsNone(parsed["period"])

    def test_woj_intensity_uses_header_counts(self) -> None:
        parsed = _parse(HEADER_HTML)
        slaskie = intensity_for_county("powiat cieszyński", "śląskie", parsed)
        podlaskie = intensity_for_county("powiat białostocki", "podlaskie", parsed)
        self.assertEqual(slaskie["woj_reports"], 87)
        self.assertEqual(podlaskie["woj_reports"], 9)
        self.assertGreater(slaskie["intensity"], podlaskie["intensity"])


if __name__ == "__main__":
    unittest.main()
