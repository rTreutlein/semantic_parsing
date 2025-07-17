!(import! &self utils)
!(import! &self setspace)
!(import! &self tvformulas)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;;In this chainer our statements look like
;($pset |- $cset)
;; $pset and $cset are sets of proofs of the form (: $term Type)

;;To add a direct proof af a type use a function that as $pset == ()
;;(() |- ((: a A)))
;;A simple function from a to b looks like:
;;(((: $a A)) |- ((: (f $a) B)))

;;This chainer requires 2 indecies to lookup atoms
;; One maps Conclusions to the Rules that prove them
;; The other maps Premises to the Rules that use them
;;They can be created with the init-kb function
(= (init-kb)
   (let* (($cs (new-space))
          ($ps (new-state (create-setspace)))
          )
   ($cs $ps))
)

(= (show-cs ($cs $ps)) (CS Element:  (match $cs $a $a)))
(= (show-ps ($cs $ps)) (sstostring (get-state $ps)))

(= (add-atom-nodup $space $atom)
   (let $elem (eval (sealed $atom (unify $space $atom $atom ())))
   (if (=alpha $elem $atom)
      ()
      (add-atom $space $atom)
   ))
)

;;When adding an atom to the KB, it is first normalized
;;Then it is added to the indexed spaces
(= (add-to-kb ($cs $ps) $nstmt)
   (let* (;($nstmt (normalize $stmt))
          (($pset |- $cset) $nstmt)
          ($f (\1 $elem (if (and (not (is-variable $elem)) (=unify $elem (CPU $fun $args $res))) () (add-atom-nodup $cs ($elem $nstmt)))))
          ($NN (map $cset $f))
          ($ss (get-state $ps))
          ($ns (insert-setspace $ss $pset $nstmt))
          ($res (change-state! $ps $ns))
          )
   (Okay))
)

;Lokup all rules that prove a conclusion
(= (lookup-ccls ($cs $ps) $ccls)
   (match $cs ($ccls $rule) ($ccls $rule)))

;Lookup all rules whose premises are a subset of $query
(= (lookup-pset-in-kb ($cs $ps) $query)
   (let $ss (get-state $ps) (combine (lookup-all-subsets $ss $query))))

;;Normalize a statement (remove premises that are part of the conclusion)
(= (normalize ()) ())
(= (normalize ($pset |- $cset))
     (let ($npset $NN $ncset) (overlap $pset $cset)
         ($npset |- (runreduction $cset))
     ))

;;Takes a list/expression of statements and combines them
(= (combine $a) (normalize (foldl1 $a unionStmt)))

;;Takes 2 statements and combines them
;;TODO should this also normalize the statements?
(= (unionStmt $stmt1 $stmt2)
   (if (or (is-variable $stmt1) (== $stmt1 ()))
     $stmt2
     (if (or (is-variable $stmt2) (== $stmt2 ()))
       $stmt1
       (let ($pset1 |- $cset1) $stmt1
         (let ($pset2 |- $cset2) $stmt2
           ((unique-union-atom $pset1 $pset2) |- (unique-union-atom $cset1 $cset2)))))))

;;;;;;;;;;;;;;;;;;;;;;
;; Backward chainer ;;
;;;;;;;;;;;;;;;;;;;;;;

;Entry point for the backward chainer
;that ensure the query is normalized
(= (bc $kb $depthNNfull $query)
 (let ($npset |- $ncset) (normalize $query)
  (if (is-variable $ncset)
   (combine (collapse (bcsingle $kb $depthNNfull ($npset |- $ncset) ())))
   (tracem finalbcout (bcset $kb $depthNNfull ($npset |- $ncset) ()))
  )
 )
)

(= (postfilter ($pset |- $cset))
 (if-decons-expr $pset $param $ptail
   (let (: $prf $NNtype $NNtv) $param
   (if (lazy-and (not (is-closed $prf)) (elemexpr $prf $cset))
     (let ($ntail |- $cset) (postfilter ($ptail |- $cset))
       ((cons-atom $param $ntail) |- $cset))
     (postfilter ($ptail |- $cset))
   ))
   ($pset |- $cset)))

!(assertEqual (postfilter (((: $prfa A atv) (: $prfb B btv)) |- ((: (something $prfa) C ctv))))
              (((: $prfa A atv)) |- ((: (something $prfa) C ctv))))

;!(postfilter (((: $a52205 A)) |- ((: (rule $a52205) B))))
;!(postfilter (((: $a52205 A)) |- ((: (rule a) B))))

;Backward chainer for a set of conclusions
(= (bcset $kb $depthNNfull ($pset |- $cset) $targets)
 (if-decons-expr $cset $ccls $ctail
  (case $ccls
   (((∧ $inner) (bcset $kb $depthNNfull ($pset |- $inner)))
    ($ccls
     ;(let ($ppset |- $pcset) (tracem sout (bcsingle $kb $depthNNfull (tracem (sin $depthNNfull) ($pset |- $ccls)) $targets))
     (let ($ppset |- $pcset) (tracem sout (combine (tracem precombine (collapse (bcsingle $kb $depthNNfull (tracem sin ($pset |- $ccls)) $targets)))))
     ;(let ($ppset |- $pcset) (combine (collapse (bcsingle $kb $depthNNfull ($pset |- $ccls) $targets)))
     (let ($ccls $otherc) (removeAlt $pcset $ccls)
     (let ($fpset |- $fcset) (tracem (pf $ctail) (postfilter ($ppset |- ($ccls))))
      (if (== $ctail ()) ;Don't recurse if there is nothing left to do
       ;($ppset |- (cons-atom $ccls $otherc)) ;TODO evalaute if it's worth to return $other
       ($fpset |- $fcset)
       (let* 
        (;(($ncset $NNcset $nctail) (overlap $pcset $ctail)) ;We could check if we have already prooved other things in $ctail but its a lot of overhead so we skip it for now
         ;($npset (concat $pset $pcset))
         ;($npcset (concat $ncset $NNcset))
         ;(($rpset |- $rcset) (bcp $kb $depthNNfull ($npset |- $nctail)))
         (($rpset |- $rcset) (bcset $kb $depthNNfull ($pset |- $ctail) $targets))
        )
        ;(normalize (unionStmt ($ppset |- $npcset) ($rpset |- $rcset)))

        (normalize (unionStmt ($fpset |- $fcset) ($rpset |- $rcset)))
        ;(unionStmt (normalize ($fpset |- $rcset)) (normalize ($rpset |- $fcset))) ;Optimized don't normalie as one
       )
      )
     )
     )
     )
    )
   )
  )
  ;$cset is empty nothing to do
  (() |- ())
 )
)

(= ((subst $kb $depth) $a) (if (== $a kb) $kb (if (== $a depth) $depth $a)))

(= (checkrev (revision $a $b)) $b)
(= (checkrev (revision $a $b)) $a)
(= (checkrev $a)
  (if-decons-expr $a $head $tail 
   (if (== $head revision)
    Empty
    $a)
   $a))

!(assertEqualToResult (checkrev (revision a b)) (a b))
!(assertEqual (checkrev (a b)) (a b))
;!(let $inp $a (if (is-variable $inp) $inp (checkrev $inp)))

;Backward chainer for a single conclusion
(= (bcsingle $kb $depthNNfull ($pset |- $ccls) $targets)
 (case $ccls
  (
   ((CPU $f $args $res)
    (if (is-closed $args)
     (let $nargs (map-expr $args (subst $kb $depthNNfull))
      (let $res (eval (cons-atom $f $nargs))
       (() |- ((CPU $f $args $res)))))
     $ccls))
   ((CPUNC $f $args $res) 
    (let $nargs (map-expr $args (subst $kb $depthNNfull))
     (let $res (eval (cons-atom $f $nargs))
      (() |- ((CPUNC $f $args $res))))))
   ((: $prf $Type $tv)
    ;Go step backwards
    (let* (
      ($nprf (if (is-variable $prf) $prf (checkrev $prf)))
      (((: $nprf $Type $tv) ($lcNNpset |- $lcNNcset)) (tt lokkup-ccls (lookup-ccls $kb (: $nprf $Type $tv)))) ;Get rule to prove $ccls
      ;(((: $nprf $Type $tv) ($lcNNpset |- $lcNNcset)) (lookup-ccls $kb (: $nprf $Type $tv))) ;Get rule to prove $ccls
      (($NNts () $NNps) (tt oat (overlapAlphaType $targets $lcNNpset)))
      (($notnededpset $opset $ppset) (tt ovlp (overlap $pset $lcNNpset))) ;Check if we have already prooved $lcNNpset
      ;(debug (trace! (Overlap $pset $lcNNpset $notnededpset $opset $ppset) debug))
     )
     ;Alternate to a forward step
     (if (== $ppset ()) ;Nothing lef to prove, return
      ;(tracem nltp ($lcNNpset |- $lcNNcset))
      ($lcNNpset |- $lcNNcset)
      ;Premises left to prove
      (unify $depthNNfull (S $depth)
       (let ($a |- $b) (tracem (bcout $ppset) (bcset $kb $depth (tracem bcin ($pset |- $ppset)) (cons-atom $ccls $targets))) ;)Proof the premises
       ;(let ($a |- $b) (bcset $kb $depth ($pset |- $ppset) (cons-atom $ccls $targets)) ;Proof the premises
        (tracem postnorm (normalize (tracem prenorm (unionStmt ($lcNNpset |- $lcNNcset) ($a |- $b))))))
        ;(unionStmt ($opset |- $lcNNcset) (tracem postnorm (normalize (tracem prenorm ($ppset |- $b)))))) ;Optimized don't need to normalize the whole thing
       (if (is-variable $pset)
        ($lcNNpset |- $lcNNcset)
        Empty))))))))

(= (merge $base $stmts)
 (if-decons-expr $stmts $stmt $rest
  (let ((: $prf1 $type1 $tv1) (: $prf2 $type2 $tv2)) ($base $stmt)
   (if (elemexpr $prf1 $prf2)
    (merge (: $prf2 $type2 $tv2) $rest)
    (if (elemexpr $prf2 $prf1)
       (merge (: $prf1 $type1 $tv1) $rest)
       (merge (: (revision $prf1 $prf2) $type1 (mergetvs $tv1 $tv2)) $rest)
    )
   )
  )
  $base
 ))

!(assertEqual (merge (: p1 (m a) (STV 0.9 0.9)) ((: p2 (m a) (STV 0.9 0.9))))
              (: (revision p1 p2) (m a) (STV 0.9 0.9473684210526316)))

(= (runreduction $stmts)
 (if-decons-expr $stmts $stmt $rest
  (unify (: $prf $type $tv) $stmt
   (if (is-variable $type)
    (let $nrest (runreduction $rest)
     (cons-atom $stmt $nrest))
    (let ($removed $remaining) (removeAlphaType $rest $stmt)
     (let $nstmt (merge $stmt $removed)
      (let $nrest (runreduction $remaining)
       (cons-atom $nstmt $nrest)))
    ))
    (let $nrest (runreduction $rest)
     (cons-atom $stmt $nrest)))
  $stmts
 )
)

!(assertEqual (runreduction ((: p1 (m a) (STV 0.9 0.9)) (: p2 (m a) (STV 0.9 0.9)) (: p3 (m b) (STV 0.9 0.9))))
              ((: (revision p1 p2) (m a) (STV 0.9 0.9473684210526316)) (: p3 (m b) (STV 0.9 0.9))))
