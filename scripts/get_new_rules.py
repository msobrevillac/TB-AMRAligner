#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
from feat2tree_v9 import *

# TODO: presume lowercase, yet should have lowercased feat.edge, etc
OP_AMR = re.compile(r':op\d+')
PREP_AMR = re.compile(r':prep\-(\S+)')
# now allowing number to be wrapped up with ""
NUMBER = re.compile(r'^"?-?[\d\.]*\d"?$')

# TODO: more rules, like 11-20, 30, etc., as well as dozen, score? four hundred, four thousand, etc
NUM2STR = { '0':['CD(zero)'],
                 '1':['DT(um)', 'DT(uma)'],
                 '2':['CD(dois)'],
                 '3':['CD(três)'],
                 '4':['CD(quatro)'],
                 '5':['CD(cinco)'],
                 '6':['CD(seis)'],
                 '7':['CD(sete)'],
                 '8':['CD(oito)'],
                 '9':['CD(nove)'],
                 '10':['CD(dez)'],
                 '11':['CD(onze)'],
                 '12':['CD(doze)'],
                 '13':['CD(treze)'],
                 '14':['CD(catorze)', 'CD(quatorze)'],
                 '15':['CD(quinze)'],
                 '16':['CD(dezesseis)'],
                 '17':['CD(dezessete)'],
                 '18':['CD(dezoito)'],
                 '19':['CD(dezenove)'],
                 '20':['CD(vinte)'],
                 '30':['CD(trinta)'],
                 '40':['CD(quarenta)'],
                 '50':['CD(cinquenta)'],
                 '60':['CD(sessenta)'],
                 '70':['CD(setenta)'],
                 '80':['CD(oitenta)'],
                 '90':['CD(noventa)'],
                 '100':['CD(cem)'],
                 '200':['CD(duzentos)'],
                 '300':['CD(trezentos)'],
                 '400':['CD(quatrocentos)'],
                 '500':['CD(quinientos)'],
                 '600':['CD(seiscentos)'],
                 '700':['CD(setecentos)'],
                 '800':['CD(oitocentos)'],
                 '900':['CD(novecentos)'],
                 '1000':['CD(mil)'],
                 '2000':['NP(CD(dois) CD(mil))'],
                 '3000':['NP(CD(três) CD(mil))'],
                 '4000':['NP(CD(quatro) CD(mil))'],
                 '5000':['NP(CD(cinco) CD(mil))'],
                 '6000':['NP(CD(seis) CD(mil))'],
                 '7000':['NP(CD(sete) CD(mil))'],
                 '8000':['NP(CD(oito) CD(mil))'],
                 '9000':['NP(CD(nove) CD(mil))'],
}

#TODO: cannot handle this (p / phone-number-entity :value 18005551212)
# in (isi_0002.13) to get 1-800-555-1212 
def get_number_rules(amr):
    '''notes:
       1) numbers, big or small, exist in various cases, not just monetary-quantity,
       or under :quant, therefore it is more general to do regex matching
       2) give integers 0-10, 100, 1000 an English option: zero, one, ..., thousand
    '''
    ret = set()
    date_entity = False
    for feat in amr.feats:
        if feat.edge == '/' and feat.node.val == 'date-entity':
            date_entity = True
            break
    for feat in amr.feats:
        if NUMBER.match(feat.node.val):
            if date_entity:
                ret |= get_date_rule(feat.node.val)
            else:
                ret |= get_quant_rule(feat.node.val)
        ret |= get_number_rules(feat.node)
    return ret

def get_date_rule(num):
    if num[0] == num[-1] == '"':
        num_rhs = num[1:-1]
    else:
        num_rhs = num
    ret = set()
    # for now, only one option
    ret.add( "qcd."+num+" -> CD("+num_rhs+")" )
    return ret

# TODO: more reasonable rules!
# TODO: some rules are commented out because lm cannot tell the better one
def get_quant_rule(num):
    if num[0] == num[-1] == '"':
        num_rhs = num[1:-1]  
    else:
        num_rhs = num 
    ret = set()
    # different ways to express num_rhs
    # rephrase num_rhs with common english expressions
    if num_rhs in NUM2STR:
        ret |= set( "qcd."+num+" -> " + i for i in NUM2STR[num_rhs])
    if re.search("\.", num_rhs):
        ret.add( "qcd."+num+" -> CD("+num_rhs+")" )
    elif len(num_rhs) < 7:
        #ret.add( "qcd."+num+" -> CD("+num+")" )
        ret.add( "qcd."+num+" -> CD("+insertComma(num_rhs)+")" )
    elif 7<= len(num_rhs) < 10:
        #ret.add( "qcd."+num+" -> CD("+insertComma(num)+")" )
        ret.add( "qcd."+num+" -> NP(CD("+insertPoint(num_rhs,6)+") NN(milhões))" )
    elif 13 > len(num_rhs) >= 10:
        #ret.add( "qcd."+num+" -> CD("+insertComma(num)+")" )
        ret.add( "qcd."+num+" -> NP(CD("+insertPoint(num_rhs,9)+") NN(bilhões))" )
    else:
        #ret.add( "qcd."+num+" -> CD("+insertComma(num)+")" )
        ret.add( "qcd."+num+" -> NP(CD("+insertPoint(num_rhs,12)+") NN(trilhões))" )
    return ret

                    
def insertPoint(cd,point_loc):
    new_cd = re.sub("\.?0+$","",cd[:-point_loc] +"."+cd[-point_loc:])
    return new_cd
    
def insertComma(num):
    triples = []
    for i in range(len(num), 0, -3):
        triples.append( num[max(0, i-3):i] )
    triples.reverse()
    return ','.join(triples)


#TODO: we can get a comprehensive list of single-word, two-word, three-word, etc. prepositions from wiki:
#http://en.wikipedia.org/wiki/List_of_English_prepositions
# TODO: why bother with qs and qnp? maybe they are not complete!
#qs.(:prep-by x0 :rest x1) -> S(qs.x1 IN(by) qnp.x0)
#qnp.(:prep-by x0 :rest x1) -> NP(qnp.x1 IN(by) qnp.x0)
# => one rule, and say lhs q, whatever it is, is inherited by the rhs q
#q.(:prep-by x0 :rest x1) -> Q(q.x1 IN(by) qnp.x0)
def get_prep_rules(amr):
    ret = set()
    for feat in amr.feats:
        ret |= get_prep_rules(feat.node)
        m = PREP_AMR.match(feat.edge)
        if m:
            split = m.group(1).split('-')
            qs_rule = 'qs.(' + feat.edge + ' x0 :rest x1) -> S(qs.x1 {0} qnp.x0)'.format(' '.join('IN(' + i + ')' for i in split))
            ret.add(qs_rule)
            qnp_rule = 'qnp.(' + feat.edge + ' x0 :rest x1) -> NP(qnp.x1 {0} qnp.x0)'.format(' '.join('IN(' + i + ')' for i in split))
            ret.add(qnp_rule)
    return ret


def get_nnp_op_rules(amr):
    ret = set()
    for feat in amr.feats:
        ret |= get_nnp_op_rules(feat.node)
    for feat in amr.feats:
        if feat.edge == '/' and feat.node.val == 'name':
            op_feats = [feat for feat in amr.feats if OP_AMR.match(feat.edge)]
            if op_feats:
                op_lhs = '/ name' + ' ' + ' '.join(feat.edge + ' x' + str(ind) for ind, feat in enumerate( op_feats ) )
                op_rhs = ' '.join('qnnp.x' + str(ind) for ind, feat in enumerate( op_feats ) )
                op_rule = 'qnp.(' + op_lhs + ') -> NP(' + op_rhs + ')' 
                ret.add(op_rule)
                for f in op_feats:
                    nnp = f.node.val[1:-1] # strip off ""
                    nnp = nnp.replace('(', '__LRB__') # xrsparse does not allow A((B))
                    nnp = nnp.replace(')', '__RRB__')
                    nnp_rule = 'qnnp.' + f.node.val + ' -> NNP(' + nnp + ')'
                    ret.add( nnp_rule )
    return ret

DASH_CONNECTED = re.compile(r'^[^\s"]+\-[^\s"]+$')
VERB_SENSE = re.compile(r'[a-zA-Z]+\-\d\d')
ENTITY_QUANTITY = ['entity', 'quantity', 'organization']

def is_entity_quantity(s):
    for ending in ENTITY_QUANTITY:
        if s.endswith(ending):
            return True
    return False

def get_dash_rules(amr):
    ret = set()
    if not amr.feats:
        if DASH_CONNECTED.match(amr.val) and not VERB_SENSE.match(amr.val) and not is_entity_quantity(amr.val):
            ret.add( 'q.' + amr.val + ' -> ' + 'q(' + ' '.join('WRD(' + i + ')' for i in amr.val.split('-') if i ) + ')' )
    for feat in amr.feats:
        ret |= get_dash_rules(feat.node)
    return ret
    

def get_new_rules(amr):

    rules = set()
    rules |= get_number_rules(amr) # :prep-x rules
    rules |= get_prep_rules(amr) # cd rules
    rules |= get_nnp_op_rules(amr) # :opx rules and qnnp rules
    rules |= get_dash_rules(amr)        
    return rules


if __name__ == '__main__':

    #TODO: parse into amr first!!!
    print get_new_rules(sys.stdin.read())
