!(import! &self utils)
!(import! &self chainer)

(= (addidx $expr $idx)
  (if-decons-expr $expr $head $tail
    (let $nhead ($head $idx)
     (let $ntail (addidx $tail (+ $idx 1))
      (cons-atom $nhead $ntail)))
    $expr))

!(assertEqual (addidx (a b c) 0) ((a 0) (b 1) (c 2)))

!(bind! sqrt (py-atom math.sqrt))

(= (out (: $NNprf $type $NNtv))
  (if-decons-expr $type $head $tail
    (if (not (is-variable $head))
      (case $head
        ((And
          (let $f (\1 ($elem $idx) (superpose ( (((: $prf $type (STV $tvs $tvc)) (CPU sqrt ($tvs) $ntvs)) |- ((: (proj $idx $prf) $elem (STV $ntvs $tvc)))) (out (: $prf $elem $tv))) ))
          (let $idtail (addidx $tail 0)
          ($f (superpose $idtail))))
         )
         (Or
          (let $f (\1 ($elem $idx) (superpose ( (((: $prf $type $tv)) |- ((: (proj $idx $prf) $elem $tv))) (out (: $prf $elem $tv)))))
          (let $idtail (addidx $tail 0)
          ($f (superpose $idtail))))
         )
        ))
      Empty)
    Empty))

;!(out (: prf (Or a b) (STV 1.0 1.0)))

(= (inTemplate $formula $head $tail)
 (let $prms (map $tail (\1 $elem (: $prf $elem $tv)))
  (let $f (\2 ($premises (: $cclprf $ccltype $ccltv)) (: $prfelem $elem $tve)
           (let (($NN1 $NN2 $NN3 $tv) $NNr) (decons-atom $premises)
            ((munion-atom $premises ((: $prfelem $elem $tve) (CPU $formula ($tv $tve) $ntv)))
             (: (cons-atom $prfelem $cclprf) (cons-atom $elem $ccltype) $ntv)
            )))
   (let ((: $fstprf $fstelem $fsttv) $rst) (decons-atom $prms)
    (let ($resNNprms (: $cclprf $ccltype $ccltv)) (foldl $rst (((: $fstprf $fstelem $fsttv)) (: ($fstprf) ($fstelem) $fsttv)) $f)
     (let ($rcclprf $rccltype) ((reverse $cclprf) (reverse $ccltype))
     ($resNNprms |- ((: (cons-atom conjunction $rcclprf) (cons-atom $head $rccltype) $ccltv)))))))))

(= (in (: $prf $type $tv))
   (if-decons-expr $type $head $tail
     (if (not (is-variable $head))
       (case $head
         ((And (inTemplate and-formula $head $tail))
          (Or (inTemplate or-formula $head $tail))
         ))
         Emtpy)
     Emtpy))

;!(in (: prf (And a b) (STV 1.0 1.0)))

(= (extract-vars-ff $accum $elem)
   (if (is-variable $elem) (cons-atom $elem $accum) $accum))

(= (extract-vars $expr) (fold-expr $expr () extract-vars-ff))

(= (subst-exists $a $b $prf)
  (let* (($avars (unique= (extract-vars $a)))
         ($bvars (unique= (extract-vars $b)))
         ($onlyb (unique= (subtraction-atom $bvars $avars))))
  (foldl-atom $onlyb $b $accum $elem (let $elem (exists $prf) $accum))
))

(= (updatePremises $premises)
  (let $temp (map-atom $premises $elem (unify $elem (: $prf (Implication $a $b) $itv) (CPU bc (kb depth ((: $prfa $a (STV 1.0 1.0)) |- (: $prfb $b $itv))) $res) $elem))
   (map-atom $temp $elem (unify $elem (: $prfa (Not $a) (STV $nas $nac)) (∧ (: $prfa $a (STV $as $ac)) (CPU - (1.0 $as) $nas)) $elem))))

(= (post ($premises |- $conclusions))
  (let $npremises (updatePremises $premises)
  (case $conclusions
    ((((: $prf ($relation $a $b) $tv))
       (if (== $relation Implication)
         (superpose ( (post ((munion-atom $npremises ((: $prfa $a $atv) (CPU mp-formula ($atv $tv) $btv))) |- ((: ($prf $prfa) $b $btv))))
                      (out $b)
                      (in $a)
                    ))
         ($npremises |- $conclusions))
     )
     (((: $prf ($relation $a) (STV $strength $confidence)))
       (if (== $relation Not)
          (post ($npremises |- ((: $prf $a (STV (- 1.0 $strength) $confidence)))))
          ($npremises |- $conclusions))
     )
     ($conclusions
      ($npremises |- $conclusions))))))


(= (postQuery ($premises |- $conclusions))
  (let $npremises (updatePremises $premises)
  (case $conclusions
    ((((: $prf ($relation $a $b) $tv))
       (if (== $relation Implication)
         (superpose ( (post ((munion-atom $npremises ((: $prfa $a $atv) (CPU mp-formula ($atv $tv) $btv))) |- ((: ($prf $prfa) $b $btv))))
                      (in $b)
                      (out $a)
                    ))
         ($npremises |- $conclusions))
     )
     (((: $prf ($relation $a) (STV $strength $confidence)))
       (if (== $relation Not)
          (post ($npremises |- ((: $prf $a (STV (- 1.0 $strength) $confidence)))))
          ($npremises |- $conclusions))
     )
     ($conclusions
      ($npremises |- $conclusions))))))

(= (convert $stmt) (unify $stmt (: $prf (WithTV $type $tv)) (: $prf $type $tv) $stmt))

(= (clean $expr)
  (unify $expr ($r $a $b)
    (if (== $r Exists) $b
    (if (== $r Forall) $b
    (if (== $r ForAll) $b
    $expr)))
  $expr))

(= (substitute $expr)
  (if (is-variable $expr)
    VAR
    (if (is-expression $expr)
      (map-atom $expr $elem (substitute $elem))
      $expr)))

(= (mcompile $stmt)
    (let $cleanstmt (convert (map-expr2 $stmt clean))
    (let (: $prf $Type $tv) $cleanstmt
    (if (is-variable $Type)
      Empty
      (case $cleanstmt
        (((: $prf ($relation $a $b) $itv)
          (if (== $relation Implication)
            (let* ( ($nb (subst-exists $a $b $prfa))
                    ($na (subst-exists $b $a $prfb))
                  )
            (post (superpose ( (((: $prfa $a $atv) (CPU mp-formula ($itv $atv) $btv))
                                |-
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
                                |-
                                ((: ((inverted $prf $pa $prfsb) $prfb) $na $natv)))
                                (out (: ((inverted $prf $pa $pb1) $pb2) $na $natv))
                                (in (: $pb2 $b $btv2))
                             ))))
            (post (superpose ( (() |- ($cleanstmt))
                  (out $cleanstmt))))
            ))
         ($cleanstmt
          (post (superpose ( (() |- ($cleanstmt))
                             (out $cleanstmt)
         ))))))))))

(= (compileQuery $stmt)
 (let (: $prf $Type $tv) (tracem pcon (convert (map-expr2 $stmt clean)))
  (if (is-variable $Type)
   ( (() |- ((: $prf $Type $tv))) ())
   (unify $Type ($relation $a $b)
    (if (== $relation Implication)
     ((postQuery (((: $prfa $a (STV 1.0 1.0))) |- ((: $prfb $b $itv))))
      (collapse (postQuery (superpose ( (in (: $prfb $b $btv)) (out (: $prfa $a $atv)) ))))
     )
     ((postQuery (() |- ((: $prf $Type $tv))))
      (collapse (postQuery (in (: $prf $Type $tv))))))
    ((postQuery (() |- ((: $prf $Type $tv))))
     (collapse (postQuery (in (: $prf $Type $tv))))))
  )))


(= (compileAdd $kb $stmt)
   (add-to-kb $kb (mcompile $stmt)))

(= (query $kb $depth $query)
   (let ($cquery $stmts) (tracem cq (compileQuery $query))
         (let $NN (collapse (add-to-kb $kb (superpose $stmts)))
            (tracem qbcout (bc $kb $depth $cquery)))))

;!(compile (: rule2 (Implication (EnchantedBook $book) (And (Reader $reader) (UnderstandsMagicalLanguages $reader $book))) (STV 1.0 1.0)))
;!(compile (: rule3 (Implication (UnderstandsMagicalLanguages $reader $book) (CanFullyAccess $reader $book)) (STV 1.0 1.0)))

;!(compileQuery (: $query (Implication a (And c (And d e))) $tv))

;(: $query (Implication (And (EnchantedBook $book) (InWhisperingLibrary $book)) (Exists ((: $reader Object)) (CanFullyAccess $reader $book))) $tv))

;!(bind! &kb (init-kb))

;!(compileAdd &kb (: stmt1 (Implication a (And b c)) (STV 0.5 0.5)))
;!(query &kb (fromNumber 5) (: $query (Implication a b) $tv))

;!(compileAdd &kb (: rule2 (Implication (EnchantedBook $book) (And (Reader $reader) (UnderstandsMagicalLanguages $reader $book))) (STV 1.0 1.0)))
;!(compileAdd &kb (: rule3 (Implication (UnderstandsMagicalLanguages $reader $book) (CanFullyAccess $reader $book)) (STV 1.0 1.0)))

;!(query &kb (fromNumber 5) (: $query (Implication (And (EnchantedBook $book) (InWhisperingLibrary $book)) (CanFullyAccess $reader $book)) $tv))

;!(compile (: rule1 (Implication a (Or b c)) (STV 1.0 1.0)))

;!(compileQuery (: $query (Implication (And (EnchantedBook $book) (InWhisperingLibrary $book)) (CanFullyAccess $reader $book)) $tv))


!(mcompile (: library-book-sale-fact1 (WithTV (And (RaisedAmount LibraryBookSale $2847) (HeldOn LibraryBookSale LastSaturday) (PopularCategory LibraryBookSale MysteryNovels)) (STV 1.0 1.0))))
