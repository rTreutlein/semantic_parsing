!(import! &self utils)
!(import! &self chainer)

(= (out (: $_prf $type $_tv))
  (if-decons-expr $type $head $tail
    (case $head
      ((And
        (let $f (\1 $elem (superpose ( (((: $prf $type (STV $tvs $tvc)) (CPU sqrt-math ($tvs) $ntvs)) ⊢ ((: (proj $prf) $elem (STV $ntvs $tvc)))) (out (: $prf $elem $tv))) ))
        ($f (superpose $tail)))
       )
       (Or
        (let $f (\1 $elem (superpose ( (((: $prf $type $tv)) ⊢ ((: (proj0 $prf) $elem $tv))) (out (: $prf $elem $tv)))))
        ($f (superpose $tail)))
       )
      ))
    Empty))

;!(out (: prf (Or a (Or b c)) (STV 1.0 1.0)))

(= (inTemplate $formula $head $tail)
 (let $prms (map $tail (\1 $elem (: $prf $elem $tv)))
  (let $f (\2 ($premises (: $cclprf $ccltype $ccltv)) (: $prfelem $elem $tve)
           (let (($_1 $_2 $_3 $tv) $_r) (decons-atom $premises)
            ((union-atom ((CPU $formula ($tv $tve) $ntv) (: $prfelem $elem $tve)) $premises)
             (: (cons-atom $prfelem $cclprf) (cons-atom $elem $ccltype) $ntv)
            )))
   (let ((: $fstprf $fstelem $fsttv) $rst) (decons-atom $prms)
    (let ($res_prms (: $cclprf $ccltype $ccltv)) (foldl $rst (((: $fstprf $fstelem $fsttv)) (: ($fstprf) ($fstelem) $fsttv)) $f)
     (let ($rres_prms $rcclprf $rccltype) ((reverse $res_prms) (reverse $cclprf) (reverse $ccltype))
     ($rres_prms ⊢ ((: (cons-atom conjunction $rcclprf) (cons-atom $head $rccltype) $ccltv)))))))))

(= (in (: $prf $type $tv))
   (if-decons-expr $type $head $tail
     (case $head
       ((And (inTemplate and-formula $head $tail))
        (Or (inTemplate or-formula $head $tail))
       ))
     Emtpy))

;!(in (: prf (And a b) (STV 1.0 1.0)))

(= (extract-vars-ff $accum $elem)
   (if (is-variable $elem) (cons-atom $elem $accum) $accum))

(= (extract-vars $expr) (fold-expr $expr () extract-vars-ff))

(= (subst-exists $a $b $prf)
  (let* (($avars (unique= (extract-vars $a)))
         ($bvars (unique= (extract-vars $b)))
         ($onlyb (unique= (subtraction-atom $bvars $avars))))
  (foldl-atom $onlyb $b $accum $elem (atom-subst (exists $prf) $elem $accum))
))

(= (updatePremises $premises)
  (let $temp (map-atom $premises $elem (unify $elem (: $prf (Implication $a $b) $itv) (CPU bc (kb depth ((: $prfa $a (STV 1.0 1.0)) ⊢ (: $prfb $b $itv))) $res) $elem))
   (map-atom $temp $elem (unify $elem (: $prfa (Not $a) (STV $nas $nac)) (∧ (: $prfa $a (STV $as $ac)) (CPU - (1.0 $as) $nas)) $elem))))

(= (post ($premises ⊢ $conclusions))
  (let $npremises (updatePremises $premises)
  (case $conclusions
    ((((: $prf (Implication $a $b) $tv))
      (superpose ( (post ((union-atom $npremises ((: $prfa $a $atv) (CPU mp-formula ($atv $tv) $btv))) ⊢ ((: ($prf $prfa) $b $btv))))
                   (out $b)
                   (in $a)
                 )
     ))
     (((: $prf (Not $a) (STV $strength $confidence)))
      (post ($npremises ⊢ ((: $prf $a (STV (- 1.0 $strength) $confidence))))))
     ($conclusions
      ($npremises ⊢ $conclusions))))))


(= (postQuery ($premises ⊢ $conclusions))
  (let $npremises (updatePremises $premises)
  (case $conclusions
    ((((: $prf (Implication $a $b) $tv))
      (superpose ( (post ((union-atom $npremises ((: $prfa $a $atv) (CPU mp-formula ($atv $tv) $btv))) ⊢ ((: ($prf $prfa) $b $btv))))
                   (in $b)
                   (out $a)
                 )
     ))
     (((: $prf (Not $a) (STV $strength $confidence)))
      (post ($npremises ⊢ ((: $prf $a (STV (- 1.0 $strength) $confidence))))))
     ($conclusions
      ($npremises ⊢ $conclusions))))))

(= (convert $stmt) (unify $stmt (: $prf (WithTV $type $tv)) (: $prf $type $tv) $stmt))

(= (clean $0)
  (let $1 (unify $0 (Exists $a $b) $b $0)
  (let $2 (unify $1 (Forall $x $y) $y $1)
          (unify $2 (ForAll $x $y) $y $2))))

(= (substitute $expr)
  (if (is-variable $expr)
    VAR
    (if (is-expression $expr)
      (map-atom $expr $elem (substitute $elem))
      $expr)))

(: rule (Implication (Dog $d) (And (Cat (exists rule $d)) (Chase $d (exists rule $d)))))

(= (compile $stmt)
    (let $cleanstmt (convert (map-expr2 $stmt clean))
    (let (: $prf $Type $tv) $cleanstmt
    (if (is-variable $Type)
      Empty
      (case $cleanstmt
        (((: $prf (Implication $a $b) $itv)
          (let* ( ($nb (subst-exists $a $b $prfa))
                  ($na (subst-exists $b $a $prfb))
                )
          (post (superpose ( (((: $prfa $a $atv) (CPU mp-formula ($itv $atv) $btv))
                              ⊢
                              ((: ($prf $prfa) $nb $btv)))
                             (out (: ($prf $prfa) $nb $btv))
                             (in (: $prfa $a $atv))

                             (((: $prfsb (substitute $b) $btv1)
                               (: $prfb $b $btv2)
                               (CPU stv< ($btv1 $btv2) True)
                               (: $pa (substitute $na) $atv)
                               (CPU inversion-formula ($atv $btv1 $itv) $nitv)
                               (CPU mp-formula ($btv2 $nitv) $natv)
                              )
                              ⊢
                              ((: ((inverted $prf $pa $prfsb) $prfb) $na $natv)))
                             (out (: ((inverted $prf $pa $pb1) $pb2) $na $natv))
                             (in (: $pb2 $b $btv2))
                           )
          ))))
         ($cleanstmt
          (post (superpose ( (() ⊢ ($cleanstmt))
                             (out $cleanstmt)
         ))))))))))

(= (compileQuery $stmt)
    (let (: $prf $Type $tv) (convert (map-expr2 $stmt clean))
    (if (is-variable $Type)
      (() ⊢ ((: $prf $Type $tv)))
      (case (: $prf $Type $tv)
        (((: $prf (Implication $a $b) $itv)
          (postQuery (superpose ( (((: $prfa $a (STV 1.0 1.0))) ⊢ ((: $prfb $b $itv)))
                             (in (: $prfb $b $btv))
                             (out (: $prfa $a $atv))
          ))))
         ((: $prf $Type $tv)
         (postQuery (superpose ( (() ⊢ ((: $prf $Type $tv)))
                                 (in (: $prf $Type $tv))
         )))))))))


(= (compileAdd $kb $stmt)
   (add-to-kb $kb (compile $stmt)))

(= (query $kb $depth $query)
   (let $stmts (tracem cq (collapse (compileQuery $query)))
      (if-decons-expr $stmts $stmt $rest
         ;(let $_ (foldl-atom $rest () $accum $elem (let $_ $accum (add-to-kb $kb $elem)))
         (let $_ (collapse (add-to-kb $kb (superpose $rest)))
            (bc $kb $depth $stmt))
         ())))

;!(compile (: rule2 (Implication (EnchantedBook $book) (And (Reader $reader) (UnderstandsMagicalLanguages $reader $book))) (STV 1.0 1.0)))
;!(compile (: rule3 (Implication (UnderstandsMagicalLanguages $reader $book) (CanFullyAccess $reader $book)) (STV 1.0 1.0)))

(: dog (Dog $d) $tvdog)

!(compile (: $query (Implication (Dog $d) (Animal $a)) $tv))

((: $prf a $tva) (CPU mp-formula ($tva $tv) $tvb) ) -> (: $prf b $tvb)

((: $prf (Dog VAR) $tva) (: $prf (Animal VAR) $tvb) (CPU inversion-formula ($tva $tvb $tv) $tvc) (: $prf (Animal $a) $tva2) (CPU mp-formula ($tva2 $tvc) $tvd)
->(: $prf (Dog $a) $tvd)

;!(compileQuery (: $query (Implication a (And c (And d e))) $tv))

;(: $query (Implication (And (EnchantedBook $book) (InWhisperingLibrary $book)) (Exists ((: $reader Object)) (CanFullyAccess $reader $book))) $tv))

;!(bind! &kb (init-kb))

;!(compileAdd &kb (: stmt1 (Implication a (And b c)) (STV 0.5 0.5)))
;!(query &kb (fromNumber 5) (: $query (Implication a b) $tv))

;!(compileAdd &kb (: rule2 (Implication (EnchantedBook $book) (And (Reader $reader) (UnderstandsMagicalLanguages $reader $book))) (STV 1.0 1.0)))
;!(compileAdd &kb (: rule3 (Implication (UnderstandsMagicalLanguages $reader $book) (CanFullyAccess $reader $book)) (STV 1.0 1.0)))

;!(query &kb (fromNumber 5) (: $query (Implication (And (EnchantedBook $book) (InWhisperingLibrary $book)) (CanFullyAccess $reader $book)) $tv))

;!(compile (: rule1 (Implication a (Or b c)) (STV 1.0 1.0)))
