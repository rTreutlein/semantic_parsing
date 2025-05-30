!(import! &self utils)
!(import! &self setspace)
!(import! &self tvformulas)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;;In this chainer our statements look like
;($pset ⊢ $cset)
;; $pset and $cset are sets of proofs of the form (: $term Type)

;;To add a direct proof af a type use a function that as $pset == ()
;;(() ⊢ ((: a A)))
;;A simple function from a to b looks like:
;;(((: $a A)) ⊢ ((: (f $a) B)))

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

(= (show-cs ($cs $ps)) (println! (CS Element:  (match $cs $a $a))))
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
          (($pset ⊢ $cset) $nstmt)
          ($f (\1 $elem (if (and (not (is-variable $elem)) (=unify $elem (CPU $fun $args $res))) () (add-atom-nodup $cs ($elem $nstmt)))))
          ($_ (map $cset $f))
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
(= (normalize ($pset ⊢ $cset))
     (let ($npset $_ $ncset) (overlap $pset $cset) ($npset ⊢ (runreduction $cset))))
     ;(let ($npset $_ $ncset) (overlap $pset $cset) ($npset ⊢ $cset)))

;;Takes a list/expression of statements and combines them
(= (combine $a) (normalize (foldl1 $a unionStmt)))

;;Takes 2 statements and combines them
;;TODO should this also normalize the statements?
(= (unionStmt $stmt1 $stmt2)
   (if (or (is-variable $stmt1) (== $stmt1 ()))
     $stmt2
     (if (or (is-variable $stmt2) (== $stmt2 ()))
       $stmt1
       (let ($pset1 ⊢ $cset1) $stmt1
         (let ($pset2 ⊢ $cset2) $stmt2
           ((unique-union-atom $pset1 $pset2) ⊢ (unique-union-atom $cset1 $cset2)))))))

;;;;;;;;;;;;;;;;;;;;;;
;; Backward chainer ;;
;;;;;;;;;;;;;;;;;;;;;;

;Entry point for the backward chainer
;that ensure the query is normalized
(= (bc $kb $depth_full $query)
 (let ($npset ⊢ $ncset) (normalize $query)
  (if (is-variable $ncset)
   (combine (collapse (bcsingle $kb $depth_full (tracem singel ($npset ⊢ $ncset) ()))))
   (bcset $kb $depth_full ($npset ⊢ $ncset) ())
  )
 )
)

(= (postfilter ($pset ⊢ $cset))
 (if-decons-expr $pset $param $ptail
   (let (: $prf $_type $_tv) $param
   (if (lazy-and (not (is-closed $prf)) (elemexpr $prf $cset))
     (let ($ntail ⊢ $cset) (postfilter ($ptail ⊢ $cset))
       ((cons-atom $param $ntail) ⊢ $cset))
     (postfilter ($ptail ⊢ $cset))
   ))
   ($pset ⊢ $cset)))

!(assertEqual (postfilter (((: $prfa A atv) (: $prfb B btv)) ⊢ ((: (something $prfa) C ctv))))
              (((: $prfa A atv)) ⊢ ((: (something $prfa) C ctv))))

!(postfilter (((: $a52205 A)) ⊢ ((: (rule $a52205) B))))
!(postfilter (((: $a52205 A)) ⊢ ((: (rule a) B))))

;Backward chainer for a set of conclusions
(= (bcset $kb $depth_full ($pset ⊢ $cset) $targets)
 (if-decons-expr $cset $ccls $ctail
  (case $ccls
   (((∧ $inner) (bcset $kb $depth_full ($pset ⊢ $inner)))
    ($ccls
     ;(let ($ppset ⊢ $pcset) (tracem sout (bcsingle $kb $depth_full (tracem (sin $depth_full) ($pset ⊢ $ccls)) $targets))
     (let ($ppset ⊢ $pcset) (tracem sout (combine (collapse (bcsingle $kb $depth_full (tracem (sin $depth_full) ($pset ⊢ $ccls)) $targets))))
     (let ($ccls $otherc) (removeAlt $pcset $ccls)
     (let ($fpset ⊢ $fcset) (postfilter ($ppset ⊢ ($ccls)))
      (if (== $ctail ()) ;Don't recurse if there is nothing left to do
       ;($ppset ⊢ (cons-atom $ccls $otherc)) ;TODO evalaute if it's worth to return $other
       ($fpset ⊢ $fcset)
       (let* 
        (;(($ncset $_cset $nctail) (overlap $pcset $ctail)) ;We could check if we have already prooved other things in $ctail but its a lot of overhead so we skip it for now
         ;($npset (concat $pset $pcset))
         ;($npcset (concat $ncset $_cset))
         ;(($rpset ⊢ $rcset) (bcp $kb $depth_full ($npset ⊢ $nctail)))
         (($rpset ⊢ $rcset) (bcset $kb $depth_full ($pset ⊢ $ctail) $targets))
        )
        ;(normalize (unionStmt ($ppset ⊢ $npcset) ($rpset ⊢ $rcset)))
        (normalize (unionStmt ($fpset ⊢ $fcset) ($rpset ⊢ $rcset)))
       )
      )
     )
     )
     )
    )
   )
  )
  ;$cset is empty nothing to do
  (() ⊢ ())
 )
)

(= ((subst $kb $depth) $a) (if (== $a kb) $kb (if (== $a depth) $depth $a)))

;Backward chainer for a single conclusion
(= (bcsingle $kb $depth_full ($pset ⊢ $ccls) $targets)
 (case $ccls
  (
   ((CPU $f $args $res)
    (if (is-closed $args)
     (let $nargs (map-expr $args (subst $kb $depth_full))
      (let $res (eval (cons-atom $f $nargs))
       (() ⊢ ((CPU $f $args $res)))))
     $ccls))
   ((CPUNC $f $args $res) 
    (let $nargs (map-expr $args (subst $kb $depth_full))
     (let $res (eval (cons-atom $f $nargs))
      (() ⊢ ((CPUNC $f $args $res))))))
   ($ccls
    (let* ;Go step backwards
     ;((($ccls ($lc_pset ⊢ $lc_cset)) (tracem lookup-ccls (lookup-ccls $kb $ccls))) ;Get rule to prove $ccls
     ((($ccls ($lc_pset ⊢ $lc_cset)) (lookup-ccls $kb $ccls)) ;Get rule to prove $ccls
      (($_ts () $_ps) (overlapAlphaType $targets $lc_pset))
      ;($oat (tracem (oat $targets $lc_pset) (overlapAlphaType $targets $lc_pset)))
      ;($oat (overlapAlphaType $targets $lc_pset))
      ;((suc) (unify ($_ts () $_ps) $oat (suc) (println! "Loop detected")))
      (($_pset $opset $ppset) (overlap $pset $lc_pset)) ;Check if we have already prooved $lc_pset
     )
     ;Alternate to a forward step
     (if (== $ppset ()) ;Nothing lef to prove, return
      ($lc_pset ⊢ $lc_cset)
      ;Premises left to prove
      (unify $depth_full (S $depth)
       (let ($a ⊢ $b) (tracem bcout (bcset $kb $depth ($pset ⊢ $ppset) (cons-atom $ccls $targets))) ;Proof the premises
        (normalize (unionStmt ($lc_pset ⊢ $lc_cset) ($a ⊢ $b))))
       (if (is-variable $pset)
        ($lc_pset ⊢ $lc_cset)
        Empty))))))))

(= (merge $base $stmts)
 (if-decons-expr $stmts $stmt $rest
  (let ((: $prf1 $type1 $tv1) (: $prf2 $type2 $tv2)) ($base $stmt)
   (if (elemexpr $prf1 $prf2)
    (: $prf2 $type2 $tv2)
    (if (elemexpr $prf2 $prf1)
     (: $prf1 $type1 $tv1)
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
