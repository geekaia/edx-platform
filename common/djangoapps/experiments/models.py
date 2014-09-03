#coding: utf-8
from django.db import models
from django.contrib.auth.models import User


"""
  by: Jacinto José Franco
  Este aquivo contem todas as entidades necessarias para fazer com que os experimentos randomizados funcionem
"""

class StrategyRandomization(models.Model):
    """
    Esta entidade armazena as definções do experimento. O que possibilita mudar do algoritmo (Operador do PlanOut) e também definir um Design
    do experimento personalizado.
    """
    # Strategy: Uniform, WeightedChoice, BernoulliTrial, RandomInteger, Block Randomization
    strategyType = models.CharField(max_length=50)

    # Lista de percents do WeightedChoice
    percents = models.CharField(max_length=50, null=True)
    probability = models.DecimalField(max_digits=2, decimal_places=2, blank=True, null=True) # Probabilidade de o bernoult trial

    # Blocos
    quantAlunos = models.IntegerField(blank=True, null=True) # exemplo 200 alunos
    tamanhoBlocos = models.IntegerField(blank=True, null=True) # 10
    quantBlocos = models.IntegerField(blank=True, null=True) # 200/10 = 20 tem que fazer a definição pelo javascript

    # Estratificada
    fatorList = models.CharField(max_length=600, null=True)
    quantAlunoStrats = models.IntegerField(blank=True, null=True)

    # PlanoutScript
    planoutScript = models.TextField(blank=True, null=True)
    planoutJson = models.TextField(blank=True, null=True)

    # Customizada --campo gerado por softwares como o JMP, SAS e R, o que possibilita criar todo tipo de randomização
    customDesign = models.TextField(blank=True, null=True)


class ExperimentDefinition(models.Model):
    """ Esta entidade habilita contém as definições de quais os experimentos. Para cada é possível ter uma linha desta tabela.

        strategy: é relacionada a tabela StrategyRandomization que possibilita definir a forma de randomização, um Script em PlanOut ou mesmo
        simplesmente alternar entre os operadores do PlanOut UniformChoice e WeightedChoice

    """
    descricao = models.CharField(max_length=60, default='meuprimeiroexperimento') # descricao do ExperimentoDeverei gerar um número ou data para a descrição
    course = models.CharField(max_length=60)
    status = models.CharField(max_length=9) # started finished paused
    userTeacher = models.ForeignKey(User)

    #algoritmo = models.CharField por enquanto só será utilizado A/B, depois pensarei nos demais
    strategy = models.ForeignKey(StrategyRandomization)


class OpcoesExperiment(models.Model):
    """
    Nesta entidade grava-se as opções do experimento. Em um teste A/B são inseridas duas versões do experimento.
    """
    experimento = models.ForeignKey(ExperimentDefinition)
    sectionExp = models.CharField(max_length=100)
    sectionExp_url = models.CharField(max_length=50)
    version = models.CharField(max_length=1) # A ou B # Se Não tiver A, então Esta inserido a versão versão A


class UserChoiceExperiment(models.Model):
    """
        Esta entidade serve para armazenar as versões definidas na randomização do aluno.
        Desta forma, o aluno sempre terá a versão que foi inicialmente definida na randomização.
    """
    userStudent = models.ForeignKey(User)
    versionExp = models.ForeignKey(OpcoesExperiment)
    bloco = models.IntegerField(blank=True)
    experimento = models.ForeignKey(ExperimentDefinition)


class HistoricoQuestoes(models.Model):
    """
        Terei que retirar esta tabela, pois o edX já implementa a função do histórico.
    """
    campo = models.CharField(max_length=600)
    valor = models.CharField(max_length=600)
    usuario = models.ForeignKey(User)


class AnonyMousPost(models.Model):
    """
        Com esta tabela aramzena-se os o id e o usuario dos comentários anônimos. Desta forma fica mais fácil para recuperar.
    """
    user = models.IntegerField()
    commentid = models.CharField(max_length=50)