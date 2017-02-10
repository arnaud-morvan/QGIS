/***************************************************************************
   qgsfieldsmappingdialog.h
    --------------------------------------
   Date                 : December 2016
   Copyright            : (C) 2016 Arnaud Morvan
   Email                : arnaud.morvan@gmail.com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************/

#ifndef QGSFIELDSMAPPINGDIALOG_H
#define QGSFIELDSMAPPINGDIALOG_H

#include <QMap>
#include <QAbstractTableModel>
#include <QDialog>

#include "qgsexpression.h"
#include "qgsfields.h"
#include "qgstablewidgetbase.h"

#include "ui_qgsfieldsmappingdialogbase.h"

typedef QMap<QString, QgsExpression> QgsFieldsMapping;

///@cond PRIVATE

/** @ingroup gui
 * Table model to edit a QVariantMap.
 * @note added in QGIS 3.0
 * @note not available in Python bindings
 */
class GUI_EXPORT QgsFieldsMappingModel : public QAbstractTableModel
{
    Q_OBJECT
  public:

    explicit QgsFieldsMappingModel( QgsFields &srcFields, QgsFields &dstFields, QObject *parent = 0 );
    QgsFieldsMapping map() const;

    int rowCount( const QModelIndex& parent = QModelIndex() ) const override;
    int columnCount( const QModelIndex& parent = QModelIndex() ) const override;
    QVariant headerData( int section, Qt::Orientation orientation, int role ) const override;
    QVariant data( const QModelIndex& index, int role = Qt::DisplayRole ) const override;
    bool setData( const QModelIndex & index, const QVariant & value, int role = Qt::EditRole ) override;
    Qt::ItemFlags flags( const QModelIndex &index ) const override;
    bool insertRows( int position, int rows, const QModelIndex & parent =  QModelIndex() ) override;
    bool removeRows( int position, int rows, const QModelIndex &parent =  QModelIndex() ) override;

    typedef QPair<QString, QgsExpression> Line;

  private:
    QVector<Line> mLines;
};
///@endcond

/** \ingroup gui
 * @brief The QgsFieldsMappingDialog class provides a input dialog for mapping between source and destination fields.
 * @note added in 3.0
 */
class GUI_EXPORT QgsFieldsMappingDialog : public QDialog, private Ui::QgsFieldsMappingDialogBase
{
    Q_OBJECT
    Q_PROPERTY( QgsFieldsMapping map READ map WRITE setMap )

  public:
    /**
     * Constructor.
     */
    explicit QgsFieldsMappingDialog(const QgsFields &srcFields, const QgsFields &dstFields, QWidget *parent = Q_NULLPTR);

    /**
     * Set the initial value of the widget.
     */
    void setMap( const QgsFieldsMapping& map );

    /**
     * Get the edit value.
     * @return the QVariantMap
     */
    QgsFieldsMapping map() const { return mModel.map(); }

  private:
    QgsFields mSrcFields;
    QgsFields mDstFields;
    QgsFieldsMappingModel mModel;
};

#endif // QGSFIELDSMAPPINGDIALOG_H
