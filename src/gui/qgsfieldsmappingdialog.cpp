/***************************************************************************
   qgsfieldsmappingdialog.cpp
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

#include "qgsfieldsmappingdialog.h"

QgsFieldsMappingDialog::QgsFieldsMappingDialog( const QgsFields &srcFields, const QgsFields &dstFields, QWidget *parent )
    : QDialog( parent )
    , mSrcFields( srcFields )
    , mDstFields( dstFields )
    , mModel( this )
{
  init( parent );
  mModel = QgsFieldsMappingModel();

  mModel.
  this->fieldsView.setModel(mModel)
}

void QgsFieldsMappingDialog::setMap( const QgsFieldsMapping& map )
{
  //removeButton->setEnabled( false );
  mModel.setMap( map );
}

///@cond PRIVATE
void QgsFieldsMappingModel::setMap( const QgsFieldsMapping& map )
{
  emit beginResetModel();
  mLines.clear();
  for ( QgsFieldsMapping::const_iterator it = map.constBegin(); it != map.constEnd(); ++it )
  {
    mLines.append( Line( it.key(), it.value() ) );
  }
  emit endResetModel();
}

QgsFieldsMapping QgsFieldsMappingModel::map() const
{
  QgsFieldsMapping ret;
  for ( QVector<Line>::const_iterator it = mLines.constBegin(); it != mLines.constEnd(); ++it )
  {
    if ( !it->first.isEmpty() )
    {
      ret[it->first] = it->second;
    }
  }
  return ret;
}

QgsFieldsMappingModel::QgsFieldsMappingModel( QObject *parent ) :
    QAbstractTableModel( parent )
{
  self._mapping = []

  for field in dp.fields():
    mLines.append(QPair(field, QgsExpression(field.name());
    self._mapping.append(self.newField(field))
    testAllExpressions()
}

int QgsFieldsMappingModel::rowCount( const QModelIndex& parent ) const
{
  Q_UNUSED( parent );
  return mLines.count();
}

int QgsFieldsMappingModel::columnCount( const QModelIndex & parent ) const
{
  Q_UNUSED( parent );
  return 2;
}

QVariant QgsFieldsMappingModel::headerData( int section, Qt::Orientation orientation, int role ) const
{
  if ( orientation == Qt::Horizontal && role == Qt::DisplayRole )
  {
    return QObject::tr( section == 0 ? "Source expression" : "Destination field" );
  }
  return QVariant();
}

QVariant QgsFieldsMappingModel::data( const QModelIndex& index, int role ) const
{
  if ( index.row() < 0 ||
       index.row() >= mLines.count() ||
       ( role != Qt::DisplayRole && role != Qt::EditRole ) )
  {
    return QVariant();
  }
  if ( index.column() == 0 )
    return mLines.at( index.row() ).first;
  if ( index.column() == 1 )
    return mLines.at( index.row() ).second.expression();
  return QVariant();
}

bool QgsFieldsMappingModel::setData( const QModelIndex & index, const QVariant & value, int role )
{
  if ( index.row() < 0 || index.row() >= mLines.count() || role != Qt::EditRole )
  {
    return false;
  }
  if ( index.column() == 0 )
  {
    mLines[index.row()].first = value.toString();
  }
  else
  {
    //mLines[index.row()].second = value;
    QgsExpression expression(value.toString());
    mLines[index.row()].second = expression;
  }
  emit dataChanged( index, index );
  return true;
}

Qt::ItemFlags QgsFieldsMappingModel::flags( const QModelIndex &index ) const
{
  return QAbstractTableModel::flags( index ) | Qt::ItemIsEditable;
}

bool QgsFieldsMappingModel::insertRows( int position, int rows, const QModelIndex & parent )
{
  Q_UNUSED( parent );
  beginInsertRows( QModelIndex(), position, position + rows - 1 );
  for ( int i = 0; i < rows; ++i )
  {
    mLines.insert( position, Line( QLatin1String( "" ), QgsExpression( QLatin1String( "" ) ) ) );
  }
  endInsertRows();
  return true;
}

bool QgsFieldsMappingModel::removeRows( int position, int rows, const QModelIndex &parent )
{
  Q_UNUSED( parent );
  beginRemoveRows( QModelIndex(), position, position + rows - 1 );
  mLines.remove( position, rows );
  endRemoveRows();
  return true;
}
///@endcond
