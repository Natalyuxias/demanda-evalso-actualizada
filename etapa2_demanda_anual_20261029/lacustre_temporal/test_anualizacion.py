"""Pruebas sintéticas de factores mensuales y conservación de componentes."""
import unittest
import numpy as np
import pandas as pd
from anualizacion_lacustre import apply_factors
class TestAnualizacion(unittest.TestCase):
 def test_residual_sin_reasignar_y_balance(self):
  m=pd.DataFrame([dict(campana='Verano',sentido_cruce='s',segmento='VL',componente='observado_asignado',flujo=4),dict(campana='Verano',sentido_cruce='s',segmento='VL',componente='residual',flujo=6)])
  f=pd.DataFrame([dict(campana='Verano',sentido_cruce='s',segmento='VL',mes=1,escenario='central',coef_mes_desde_flujo_fecha=3)])
  q=apply_factors(m,f)
  self.assertEqual(q.flujo_anualizado_mes.sum(),30)
  self.assertEqual(q.loc[q.componente.eq('residual'),'flujo_anualizado_mes'].iloc[0],18)
 def test_faltante_no_cero(self):
  m=pd.DataFrame([dict(campana='Verano',sentido_cruce='s',segmento='OTRO',componente='residual',flujo=np.nan)])
  f=pd.DataFrame([dict(campana='Verano',sentido_cruce='s',segmento='OTRO',mes=1,escenario='central',coef_mes_desde_flujo_fecha=3)])
  self.assertTrue(apply_factors(m,f).flujo_anualizado_mes.isna().all())
 def test_duplicado_temporal_detectado(self):
  m=pd.DataFrame([dict(campana='Verano',sentido_cruce='s',segmento='VL',flujo=4)])
  f=pd.DataFrame([dict(campana='Verano',sentido_cruce='s',segmento='VL',mes=1,escenario='central',coef_mes_desde_flujo_fecha=3)]*2)
  with self.assertRaises(AssertionError):apply_factors(m,f)
 def test_unidad_sin_perfil_no_se_pierde_silenciosamente(self):
  m=pd.DataFrame([dict(campana='Verano',sentido_cruce='s',segmento='CAM',flujo=4)])
  f=pd.DataFrame([dict(campana='Verano',sentido_cruce='s',segmento='VL',mes=1,escenario='central',coef_mes_desde_flujo_fecha=3)])
  with self.assertRaises(AssertionError):apply_factors(m,f)
if __name__=='__main__':unittest.main()
