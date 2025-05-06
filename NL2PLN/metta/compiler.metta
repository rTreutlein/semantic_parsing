!(import! &self utils)
;!(import! &self chainer)

(= (out (: $_prf $type $_tv))
  (if-decons-expr $type $head $tail
    (case $head
      ((And
        (let $f (\1 $elem (superpose ( (((: $prf $type (STV $tvs $tvc)) (CPU sqrt-math ($tvs) $ntvs)) ⊢ ((: (proj0 $prf) $elem (STV $ntvs $tvc)))) (out (: $prf $elem $tv))) ))
        (let $tmp (superpose $tail) ($f $tmp)))
       )
       (Or
        (let $f (\1 $elem (superpose ( (((: $prf $type $tv)) ⊢ ((: (proj0 $prf) $elem $tv))) (out (: $prf $elem $tv)))))
        (let $tmp (superpose $tail) ($f $tmp)))
       )
      ))
    Empty))

(= (inTemplate $formula $type $tail)
 (let $prms (map $tail (\1 $elem (: $prf $elem $tv)))
  (let $f (\2 ($premises (: $cclprf $ccltype $ccltv)) (: $prfelem $elem $tve)
           (let (($_1 $_2 $_3 $tv) $_r) (decons-atom $premises)
            ((union-atom ((CPU $formula ($tv $tve) $ntv) (: $prfelem $elem $tve)) $premises)
             (: (cons-atom $prfelem $cclprf) $_ $ntv)
            )))
   (let ($fst $rst) (decons-atom $prms)
    (let ($res_prms (: $cclprf $ccltype $ccltv)) (myfold-atom $rst (($fst) (: () _ _)) $f)
     ((reverse $res_prms) ⊢ ((: (cons-atom conjunction $cclprf) $type $ccltv))))))))

(= (in (: $prf $type $tv))
   (if-decons-expr $type $head $tail
     (case $head
       ((And (inTemplate and-formula $type $tail))
        (Or (inTemplate or-formula $type $tail))
       ))
     Emtpy))

(= (extract-vars-ff $accum $elem)
   (if (is-variable $elem) (cons-atom $elem $accum) $accum))

(= (extract-vars $expr) (fold-expr $expr () extract-vars-ff))

(= (subst-exists $a $b $prf)
  (let* (($avars (extract-vars $a))
         ($bvars (extract-vars $b))
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

(= (compile $stmt)
    (let $cleanstmt (convert (map-expr2 $stmt clean))
    (case $cleanstmt
      (((: $prf (Implication $a $b) $itv)
        (let* ( ($nb (subst-exists $a $b $prfa))
              )
        (post (superpose ( (((: $prfa $a $atv) (CPU mp-formula ($itv $atv) $btv)) ⊢ ((: ($prf $prfa) $nb $btv)))
                           (tracem out (out (: ($prf $prfa) $nb $btv)))
                           (in (: $prfa $a $atv))
        )))))
       ($cleanstmt
        (post (superpose ( (() ⊢ ($cleanstmt))
                           (out $cleanstmt)
       ))))))))

(= (compileQuery $stmt)
    (let $cleanstmt (convert (map-expr2 $stmt clean))
    (case $cleanstmt
      (((: $prf (Implication $a $b) $itv)
        (postQuery (superpose ( (((: $prfa $a (STV 1.0 1.0))) ⊢ ((: $prfb $b $itv)))
                           (in (: $prfb $b $btv))
                           (out (: $prfa $a $atv))
        ))))
       ($cleanstmt
       (postQuery (superpose ( (() ⊢ ($cleanstmt))
                               (out $cleanstmt)
       ))))))))


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

;!(compile (: $query (Implication a (And b (And c d))) $tv))
;!(compileQuery (: $query (Implication a (And c (And d e))) $tv))

;(: $query (Implication (And (EnchantedBook $book) (InWhisperingLibrary $book)) (Exists ((: $reader Object)) (CanFullyAccess $reader $book))) $tv))

;!(bind! &kb (init-kb))

;!(compileAdd &kb (: stmt1 (Implication a (And b c)) (STV 0.5 0.5)))
;!(query &kb (fromNumber 5) (: $query (Implication a b) $tv))

;!(compileAdd &kb (: rule2 (Implication (EnchantedBook $book) (And (Reader $reader) (UnderstandsMagicalLanguages $reader $book))) (STV 1.0 1.0)))
;!(compileAdd &kb (: rule3 (Implication (UnderstandsMagicalLanguages $reader $book) (CanFullyAccess $reader $book)) (STV 1.0 1.0)))

;!(query &kb (fromNumber 5) (: $query (Implication (And (EnchantedBook $book) (InWhisperingLibrary $book)) (CanFullyAccess $reader $book)) $tv))

!(compile (: rule1 (Implication a (Or b (Or c x))) (STV 1.0 1.0)))
