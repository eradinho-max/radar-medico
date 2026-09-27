import unittest
from datetime import datetime

from collector.src.modelos import Ficha
from collector.src.classificador import eh_medico
from collector.src import banco


class ClassificadorTests(unittest.TestCase):
    def test_famesp_tecnico_nao_e_medico(self):
        f = Ficha(
            id="x",
            titulo="FAMESP - SP abre processos seletivos para profissionais de nível técnico em Bauru",
            orgao="Fundação para o Desenvolvimento Médico e Hospitalar",
            cargo="Técnico em enfermagem",
        )
        self.assertFalse(eh_medico(f))

    def test_medico_psiquiatra_e_medico(self):
        f = Ficha(id="x", titulo="Concurso público", cargo="Médico Psiquiatra")
        self.assertTrue(eh_medico(f))

    def test_orgao_medico_sozinho_nao_basta(self):
        f = Ficha(id="x", titulo="Processo seletivo para profissionais", orgao="Centro Médico Estadual", cargo="Técnico")
        self.assertFalse(eh_medico(f))


class BancoTests(unittest.TestCase):
    def test_item_inalterado_preserva_timestamps(self):
        dados = {"itens": {}, "mudancas": []}
        f1 = Ficha(id="u1", titulo="Médico Psiquiatra", orgao="Prefeitura X", uf="AL", cargo="Médico Psiquiatra")
        novos, atualizacoes = banco.comparar([f1], dados)
        self.assertEqual(len(novos), 1)
        self.assertEqual(atualizacoes, [])
        banco.incorporar([f1], dados)

        primeira = dados["itens"]["u1"]["primeira_vez"]
        ultima = dados["itens"]["u1"]["ultima_atualizacao"]

        f2 = Ficha(id="u1", titulo="Médico Psiquiatra", orgao="Prefeitura X", uf="AL", cargo="Médico Psiquiatra")
        novos2, atualizacoes2 = banco.comparar([f2], dados)
        self.assertEqual(novos2, [])
        self.assertEqual(atualizacoes2, [])
        banco.incorporar([f2], dados)

        self.assertEqual(dados["itens"]["u1"]["primeira_vez"], primeira)
        self.assertEqual(dados["itens"]["u1"]["ultima_atualizacao"], ultima)
        self.assertIn("u1", dados["itens"])

    def test_url_nova_similar_vira_possivel_retificacao(self):
        agora = datetime.now().isoformat(timespec="seconds")
        dados = {"itens": {
            "antiga": Ficha(
                id="antiga",
                titulo="Concurso Médico Psiquiatra 2026",
                orgao="Prefeitura X",
                uf="AL",
                cargo="Médico Psiquiatra",
                primeira_vez=agora,
                ultima_atualizacao=agora,
            ).to_dict()
        }, "mudancas": []}

        nova = Ficha(
            id="nova",
            titulo="Concurso Médico Psiquiatra 2026 - Retificação",
            orgao="Prefeitura X",
            uf="AL",
            cargo="Médico Psiquiatra",
        )
        novos, atualizacoes = banco.comparar([nova], dados)

        self.assertEqual(novos, [])
        self.assertEqual(len(atualizacoes), 1)
        self.assertEqual(atualizacoes[0]["possivel_retificacao_de"], "antiga")
        self.assertIn("possível retificação", nova.flags)


if __name__ == "__main__":
    unittest.main()
